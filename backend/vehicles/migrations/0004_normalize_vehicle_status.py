from django.db import migrations, models


STATUS_NORMALIZATION_MAP = {
    'available': 'available',
    'booked': 'booked',
    'rented': 'booked',
    'da dat': 'booked',
    'in_use': 'in_use',
    'in use': 'in_use',
    'in operation': 'in_use',
    'dang hoat dong': 'in_use',
    'maintenance': 'maintenance',
    'bao tri': 'maintenance',
}


def normalize_vehicle_statuses(apps, schema_editor):
    Vehicle = apps.get_model('vehicles', 'Vehicle')
    for vehicle in Vehicle.objects.all():
        raw = (vehicle.status or '').strip().lower()
        normalized = STATUS_NORMALIZATION_MAP.get(raw, 'available')
        if vehicle.status != normalized:
            vehicle.status = normalized
            vehicle.save(update_fields=['status'])


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0003_alter_vehicle_status'),
    ]

    operations = [
        migrations.RunPython(normalize_vehicle_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='vehicle',
            name='status',
            field=models.CharField(
                choices=[
                    ('available', 'Available'),
                    ('booked', 'Booked'),
                    ('in_use', 'In Use'),
                    ('maintenance', 'Maintenance'),
                ],
                default='available',
                max_length=20,
            ),
        ),
    ]
