"""

Exports a collection as CSV

T. Kim Nguyen <nguyen@uwosh.edu> 2014-09-30

Outputs all the columns selected in the collection, plus all fields in the Dexterity objects returned by the collection.

Warning: respects the collection's limit on the number of returned results, in case you're wondering why this code outputs 
just (say) 10 rows.

Based on SmartCsvExporterTool.

How to use this: go to ZMI -> portal_skins -> custom and add a new External Method:

    ID: export_as_csv
    Module Name: export_as_csv
    Function Name: export_as_csv

To have this "Export as CSV" tab show up on all collections, 
go to the ZMI -> portal_actions -> object and create a new CMFAction with:

    Title: Export to CSV
    URL: string:export_as_csv
    Condition: python: object.Type() == 'Collection'
    Permissions: View
    Visible? True

"""

import csv, time
from cStringIO import StringIO
from plone.app.textfield.value import RichTextValue

## Define properties
_properties = ({'id': 'csv_options', 'type': 'lines', 'mode': 'rw', "label":"CSV writer additionnal options (option:[type:]value) type may be int, float or csv (for csv module constants)"},)

csv_options = ["quoting:csv:QUOTE_ALL",]

def get_csv_options():
    """ get csv options as a dict from csv_options property """
    result = dict()
    csv_options = ["quoting:csv:QUOTE_ALL",]
    for o in csv_options:
        optInfo = o.split(':')
        if len(optInfo) > 2:
            optType = optInfo.pop(1)
            if optType == 'int':
                optInfo[1] = int(optInfo[1])
            if optType == 'float':
                optInfo[1] = float(optInfo[1])
            if optType == 'csv':
                optInfo[1] = csv.__dict__[optInfo[1]]
        if o:
           result[optInfo[0]] = optInfo[1]
    return result


def export_csv(name, data, RESPONSE):
    """
    Do a CSV export from a Python list
    """
    buffer = StringIO()
    options = get_csv_options()

    writer = csv.writer(buffer, **options)
    for row in data:
        writer.writerow(row)
    value = buffer.getvalue()
    value = unicode(value, "utf-8").encode("iso-8859-1", "replace")
    RESPONSE.setHeader('Content-Type', 'text/csv')
    RESPONSE.setHeader('Content-Disposition', 'attachment;filename=%s-%s.csv' % (name, time.strftime("%Y%m%d-%H%M")))
    return value

def export_as_csv(self):
    """
    Modify keywords of object
    """

    def processEntry(entry):
        """
        some processing to clean up entries
        """
        if not entry:
            return ''

        # normalize to list
        result = []
        if not isinstance(entry, (list, tuple)):
            entry = [entry,]
        for e in entry:
            if e is None:
                e = ''
            elif not isinstance(e, str) and hasattr(e, 'Title'):
                e = e.Title()
            elif isinstance(e, unicode):
                e = e.encode('utf-8')
            elif not isinstance(e, str):
                e = str(e)
            result.append(e)
        return "\n".join(result)

    fields = self.getCustomViewFields()

    vocab = self.listMetaDataFields(False)
    items = self.queryCatalog(b_size=1000)

    # get the fields to grab
    from zope.app.content import queryContentType
    from zope.schema import getFieldsInOrder
    firstobj = items[0].getObject()
    schema = queryContentType(firstobj)
    extrafields = tuple([f[0] for f in getFieldsInOrder(schema)])

    fields += extrafields
    data = [ [ vocab.getValue(field, field) for field in fields ] ]
    for item in items:
        line = [ getattr(item, field, "") for field in fields if field not in extrafields]

        # handle all the other Dexterity object fields.
        # this will be slow but it probably won't be run frequently
        obj = item.getObject()
        # handle RichTextValue fields differently
        for field in extrafields:
            value = getattr(obj, field, "")
            if isinstance(value, RichTextValue):
                line += [value.raw]
            else:
                line += [value]

        # make entries exportable
        line = [processEntry(e) for e in line]
        data.append(line)

    return export_csv(self.getId(), data, self.REQUEST.RESPONSE)

