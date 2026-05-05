from django.db import models


class NamedLookupModel(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        abstract = True


class StoreBrand(NamedLookupModel):
    class Meta:
        db_table = "store_brands"


class StoreType(NamedLookupModel):
    class Meta:
        db_table = "store_types"


class City(NamedLookupModel):
    class Meta:
        db_table = "cities"


class State(NamedLookupModel):
    class Meta:
        db_table = "states"


class Country(NamedLookupModel):
    class Meta:
        db_table = "countries"


class Region(NamedLookupModel):
    class Meta:
        db_table = "regions"


class Store(models.Model):
    store_id = models.CharField(max_length=255, unique=True)
    store_external_id = models.CharField(max_length=255, default="", blank=True)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    store_brand = models.ForeignKey(StoreBrand, null=True, blank=True, on_delete=models.SET_NULL)
    store_type = models.ForeignKey(StoreType, null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.SET_NULL)
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"


class User(models.Model):
    USER_TYPE_CHOICES = ((1, "1"), (2, "2"), (3, "3"), (7, "7"))

    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, default="", blank=True)
    last_name = models.CharField(max_length=150, default="", blank=True)
    email = models.CharField(max_length=254)
    user_type = models.IntegerField(default=1, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=32, default="", blank=True)
    supervisor = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"


class PermanentJourneyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "permanent_journey_plans"
        constraints = [
            models.UniqueConstraint(fields=["user", "store", "date"], name="uq_pjp_user_store_date"),
        ]
