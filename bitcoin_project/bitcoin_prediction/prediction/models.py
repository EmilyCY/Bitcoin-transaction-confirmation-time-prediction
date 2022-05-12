from django.db import models

# Create your models here.
class Transaction(models.Model):
    index_of_transaction = models.IntegerField()
    number_of_inputs = models.IntegerField()
    number_of_outputs = models.IntegerField()
    version_of_transaction = models.IntegerField()
    size_of_transaction = models.IntegerField()
    weight_of_transaction = models.IntegerField()
    received_timestamp_of_transaction = models.IntegerField()
    relay_node = models.IntegerField()
    locktime_in_transaction = models.IntegerField()
    transaction_fee = models.FloatField()
    confirmed_block_height = models.IntegerField()
    index_of_confirmed_block_height = models.IntegerField()
    confirmed_timestamp_of_transaction = models.IntegerField()
    waiting_time_of_transaction = models.FloatField()
    feerate_of_transaction = models.FloatField()
    enter_block_height = models.IntegerField()
    waiting_block_number = models.IntegerField()
    valid_time_intx = models.FloatField()
    valid_block_intx = models.IntegerField()
    valid_waiting = models.FloatField()
    last_block_interval_intx = models.FloatField()

    class Meta:
        db_table = 'transaction'

class Simulation(models.Model):
    priority_group = models.IntegerField()
    fee_rate = models.FloatField(default=0)
    estimated_waiting_time = models.FloatField(default=0)

    def __str__(self) -> str:
        return str(self.estimated_waiting_time)

def my_function():
    return 0