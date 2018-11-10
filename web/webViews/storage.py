from flask import session, redirect, request
from webViews.view import normalView
from webViews.log import logger
from webViews.checkname import checkname
from webViews.dockletrequest import dockletRequest

class StorageListView(normalView):
    template_path = "storage/list.html"

    @classmethod
    def get(self):
        masterips = dockletRequest.post_to_all()
        result = dockletRequest.post('/storage/list/', {}, masterips[0].split("@")[0]).get('all_dataset')
        all_dataset = {}
        if result.get('status'):
            all_dataset = result.get('data')
        return self.render(self.template_path, all_dataset=all_dataset)


class CreateDataSetView(normalView):
    @classmethod
    def post(self):
        return redirect('/storage/')

class UpdateDataSetView(normalView):
    @classmethod
    def get(self):
        #dataset_name = self.dataset_name
        return redirect('/storage/')

class ImportDataSetView(normalView):
    @classmethod
    def get(self):
        # dataset_name = self.dataset_name
        return redirect('/storage/')

class DeleteDataSetView(normalView):
    @classmethod
    def get(self):
        # dataset_name = self.dataset_name
        return redirect('/storage/')

class ShareDataSetView(normalView):
    @classmethod
    def get(self):
        return redirect('/storage/')