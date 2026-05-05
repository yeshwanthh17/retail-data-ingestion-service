from dataclasses import dataclass
from typing import List, Optional, Set

from ingestion.models import User
from ingestion.services.base import BaseIngestionProcessor, IngestionType, USER_FIELD_ALIASES, VALID_USER_TYPES
from ingestion.utils.normalization import is_valid_phone_number


@dataclass
class PreparedUser:
    row_number: int
    username: str
    first_name: str
    last_name: str
    email: str
    user_type: int
    phone_number: str
    supervisor_username: str
    supervisor_id: Optional[int]
    is_active: bool


class UserIngestionProcessor(BaseIngestionProcessor):
    def ingest(self, upload) -> dict:
        errors: List[dict] = []
        processed_rows = 0
        existing_usernames = self._load_existing_usernames()
        existing_user_ids = self._load_existing_user_ids()
        file_usernames: Set[str] = set()
        candidates: List[PreparedUser] = []

        raw_rows = list(self._enumerate_rows(upload))
        for row_number, row in raw_rows:
            processed_rows += 1
            row_errors: List[dict] = []
            username = self._required_string(row, row_number, "username", USER_FIELD_ALIASES, 150, row_errors)
            first_name = self._optional_string(row, "first_name", USER_FIELD_ALIASES, 150, row_number, row_errors)
            last_name = self._optional_string(row, "last_name", USER_FIELD_ALIASES, 150, row_number, row_errors)
            email = self._required_email(row, row_number, row_errors)
            user_type = self._parse_int(row, row_number, "user_type", USER_FIELD_ALIASES, row_errors, default=1)
            phone_number = self._optional_string(row, "phone_number", USER_FIELD_ALIASES, 32, row_number, row_errors)
            supervisor_username = self._optional_string(row, "supervisor_username", USER_FIELD_ALIASES, 150, row_number, row_errors)
            supervisor_id = self._parse_optional_int(row, row_number, "supervisor_id", USER_FIELD_ALIASES, row_errors)
            is_active = self._parse_bool(row, row_number, "is_active", USER_FIELD_ALIASES, row_errors, default=True)

            if username and username in existing_usernames.union(file_usernames):
                row_errors.append(self._error(row_number, "username", "Duplicate username in file or database.", username))
            if user_type is not None and user_type not in VALID_USER_TYPES:
                row_errors.append(self._error(row_number, "user_type", "Allowed values are 1, 2, 3, 7.", str(user_type)))
            if phone_number and not is_valid_phone_number(phone_number):
                row_errors.append(self._error(row_number, "phone_number", "Invalid phone number format.", phone_number))
            if supervisor_username and supervisor_username == username:
                row_errors.append(self._error(row_number, "supervisor_username", "User cannot supervise themselves.", supervisor_username))
            if supervisor_id is not None and supervisor_id not in existing_user_ids:
                row_errors.append(self._error(row_number, "supervisor_id", "Supervisor id does not exist in database.", str(supervisor_id)))

            if row_errors:
                errors.extend(row_errors)
                continue

            file_usernames.add(username)
            candidates.append(
                PreparedUser(
                    row_number=row_number,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    user_type=user_type or 1,
                    phone_number=phone_number,
                    supervisor_username=supervisor_username,
                    supervisor_id=supervisor_id,
                    is_active=is_active,
                )
            )

        valid_candidates = self._filter_supervisor_consistent_candidates(candidates, existing_usernames, errors)
        if valid_candidates:
            User.objects.bulk_create(
                [
                    User(
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                        user_type=user.user_type,
                        phone_number=user.phone_number,
                        is_active=user.is_active,
                    )
                    for user in valid_candidates
                ],
                batch_size=self.batch_size,
            )
            self._resolve_supervisors(valid_candidates)

        return self._build_summary(
            IngestionType.USERS,
            upload.name,
            processed_rows,
            len(valid_candidates),
            errors,
            {"batch_size": self.batch_size, "strategy": "validate_then_bulk_create_and_bulk_update"},
        )

    def _filter_supervisor_consistent_candidates(self, candidates: List[PreparedUser], existing_usernames: Set[str], errors: List[dict]) -> List[PreparedUser]:
        candidates_by_username = {candidate.username: candidate for candidate in candidates}
        valid_usernames = set(candidates_by_username)
        invalidated: Set[str] = set()

        changed = True
        while changed:
            changed = False
            for username in list(valid_usernames):
                candidate = candidates_by_username[username]
                if not candidate.supervisor_username:
                    continue
                if candidate.supervisor_username in existing_usernames or candidate.supervisor_username in valid_usernames:
                    continue
                valid_usernames.remove(username)
                invalidated.add(username)
                changed = True

        for username in invalidated:
            candidate = candidates_by_username[username]
            errors.append(
                self._error(
                    candidate.row_number,
                    "supervisor_username",
                    "Supervisor username does not exist in database or among valid uploaded users.",
                    candidate.supervisor_username,
                )
            )

        return [candidate for candidate in candidates if candidate.username in valid_usernames]

    def _resolve_supervisors(self, users: List[PreparedUser]) -> None:
        username_to_id = {username: user_id for user_id, username in User.objects.values_list("id", "username")}
        updates = []
        for user in users:
            if not user.supervisor_username and user.supervisor_id is None:
                continue
            db_user = User.objects.get(username=user.username)
            db_user.supervisor_id = user.supervisor_id or username_to_id.get(user.supervisor_username)
            updates.append(db_user)
        if updates:
            User.objects.bulk_update(updates, ["supervisor"], batch_size=self.batch_size)
