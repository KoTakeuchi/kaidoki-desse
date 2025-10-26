from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0008_notificationevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationevent",
            name="sent_flag",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="notificationevent",
            name="sent_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
