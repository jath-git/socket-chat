class FirebaseService:
    def __init__(self, db):
        self.db = db
        self.document_created = False

    # crud operations on firebase db
    def create_document(self, doc):
        reference = self.db.collection('servers').document(doc)
        self.reference = reference
        self.document_created = True

    def set_document(self, obj):
        if not self.document_created:
            return
        self.reference.set(obj)

    def read_document(self):
        if not self.document_created:
            return
        return self.reference.get().to_dict()

    def read_document_field(self, field):
        if not self.document_created:
            return
        doc = self.read_document()
        if field in doc:
            return doc[field]
        else:
            return None
    
    def update_document(self, key, value):
        if not self.document_created:
            return
        self.reference.update({key: value})

    def update_document_int(self, key, increment):
        if not self.document_created:
            return
        curr_value = self.read_document_field(key)
        if curr_value == None:
            return
        self.update_document(key, curr_value + increment)


    def delete_document(self):
        if not self.document_created:
            return
        self.sreference.delete()
    
