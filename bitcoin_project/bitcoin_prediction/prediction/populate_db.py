from .models import Transaction

from collections import defaultdict
from django.apps import apps
import os, csv

class BulkCreateManager(object):
    """
    This helper class keeps track of ORM objects to be created for multiple
    model classes, and automatically creates those objects with `bulk_create`
    when the number of objects accumulated for a given model class exceeds
    `chunk_size`.
    Upon completion of the loop that's `add()`ing objects, the developer must
    call `done()` to ensure the final set of objects is created for all models.
    """

    def __init__(self, chunk_size=100):
        self._create_queues = defaultdict(list)
        self.chunk_size = chunk_size

    def _commit(self, model_class):
        model_key = model_class._meta.label
        model_class.objects.bulk_create(self._create_queues[model_key])
        self._create_queues[model_key] = []

    def add(self, obj):
        #Add an object to the queue to be created, and call bulk_create if we have enough objs.
        model_class = type(obj)
        model_key = model_class._meta.label
        self._create_queues[model_key].append(obj)
        if len(self._create_queues[model_key]) >= self.chunk_size:
            self._commit(model_class)

    def done(self):
        # Always call this upon completion to make sure the final partial chunk is saved.
        for model_name, objs in self._create_queues.items():
            if len(objs) > 0:
                self._commit(apps.get_model(model_name))

def load_data(request):
    scriptpath = os.path.dirname(os.getcwd())
    filename = os.path.join(scriptpath, 'bitcoin_prediction/static/data/TimetxinBlock622500.csv')
    
    with open(filename, 'r') as csv_file:
        bulk_mgr = BulkCreateManager(chunk_size=20)
        for row in csv.reader(csv_file):
            bulk_mgr.add(Transaction(   index = row[0],
                                        inputs = row[1],
                                        outputs = row[2],
                                        trans_version = row[3],
                                        trans_size = row[4],
                                        trans_weight = row[5],
                                        received_time = row[6],
                                        relay_node = row[7],
                                        locktime = row[8],
                                        trans_fee = row[9],
                                        confirmed_block_height = row[10],
                                        index_block_height = row[11],
                                        confirm_time = row[12],
                                        waiting_time = row[13],
                                        feerate = row[14],
                                        enter_block_height = row[15],
                                        waiting_block_num = row[16],
                                        valid_time = row[17],
                                        valid_block_height = row[18],
                                        valid_waiting = row[19],
                                        last_block_interval = row[20]))
        bulk_mgr.done()