from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="City",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
            options={"db_table": "cities"},
        ),
        migrations.CreateModel(
            name="Country",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
            options={"db_table": "countries"},
        ),
        migrations.CreateModel(
            name="Region",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
            options={"db_table": "regions"},
        ),
        migrations.CreateModel(
            name="State",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
            options={"db_table": "states"},
        ),
        migrations.CreateModel(
            name="StoreBrand",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
            options={"db_table": "store_brands"},
        ),
        migrations.CreateModel(
            name="StoreType",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
            options={"db_table": "store_types"},
        ),
        migrations.CreateModel(
            name="Store",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("store_id", models.CharField(max_length=255, unique=True)),
                ("store_external_id", models.CharField(blank=True, default="", max_length=255)),
                ("name", models.CharField(max_length=255)),
                ("title", models.CharField(max_length=255)),
                ("latitude", models.FloatField(default=0.0)),
                ("longitude", models.FloatField(default=0.0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("modified_on", models.DateTimeField(auto_now=True)),
                ("city", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.city")),
                ("country", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.country")),
                ("region", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.region")),
                ("state", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.state")),
                ("store_brand", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.storebrand")),
                ("store_type", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.storetype")),
            ],
            options={"db_table": "stores"},
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=150, unique=True)),
                ("first_name", models.CharField(blank=True, default="", max_length=150)),
                ("last_name", models.CharField(blank=True, default="", max_length=150)),
                ("email", models.CharField(max_length=254)),
                ("user_type", models.IntegerField(choices=[(1, "1"), (2, "2"), (3, "3"), (7, "7")], default=1)),
                ("phone_number", models.CharField(blank=True, default="", max_length=32)),
                ("is_active", models.BooleanField(default=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("modified_on", models.DateTimeField(auto_now=True)),
                ("supervisor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.user")),
            ],
            options={"db_table": "users"},
        ),
        migrations.CreateModel(
            name="PermanentJourneyPlan",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("modified_on", models.DateTimeField(auto_now=True)),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="ingestion.store")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="ingestion.user")),
            ],
            options={"db_table": "permanent_journey_plans"},
        ),
        migrations.AddConstraint(
            model_name="permanentjourneyplan",
            constraint=models.UniqueConstraint(fields=("user", "store", "date"), name="uq_pjp_user_store_date"),
        ),
    ]
