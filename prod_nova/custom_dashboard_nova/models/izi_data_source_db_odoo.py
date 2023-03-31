# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class IziDataSourceDBOdoo (models.Model):
    _inherit = 'izi.data.source'
    
    def get_source_tables_db_odoo(self, **kwargs):
        self.ensure_one()

        Table = self.env['izi.table']
        Field = self.env['izi.table.field']

        table_by_name = kwargs.get('table_by_name')
        field_by_name = kwargs.get('field_by_name')

        # Get Tables
        domain = [('transient', '=', False)]
        if self.table_filter:
            table_filters = self.table_filter.split(',')
            table_filters = [tf.strip().replace('_', '.') for tf in table_filters]
            domain.append(('model', 'in', table_filters))
        models = self.env['ir.model'].search(domain)
        for model in models:
            table_name = model.model.replace('.', '_')
            table_desc = model.name

            # Create or Get Tables
            table = table_by_name.get(table_name)
            if table_name not in table_by_name:
                table = Table.create({
                    'active': True,
                    'name': table_desc,
                    'table_name': table_name,
                    'source_id': self.id,
                    'is_stored': False,
                    'user_defined': False,
                    'model_id': model.id,
                })
                field_by_name[table_name] = {}
            else:
                table.write({
                    'active': True,
                    'name': table_desc,
                    'table_name': table_name,
                    'source_id': self.id,
                    'is_stored': False,
                    'user_defined': False,
                    'model_id': model.id,
                })
                table_by_name.pop(table_name)
            
            # Get Fields
            field_type_mapping = {
                'datetime': 'datetime',
                'boolean': 'boolean',
                'monetary': 'number',
                'char': 'string',
                'many2one': 'foreignkey',
                'integer': 'number',
                'one2many': 'foreignkey',
                'many2many': 'foreignkey',
                'date': 'date',
                'selection': 'string',
                'text': 'string',
                'float': 'number',
                'binary': 'byte',
            }
            for field in model.field_id:
                title = field.field_description
                field_name = field.name
                ttype = field.ttype
                if ttype not in field_type_mapping:
                    continue
                field_type = field_type_mapping[ttype]
                foreign_table = False
                foreign_column = False
                if ttype == 'many2one':
                    foreign_table = field.relation
                    foreign_column = 'id'
                # Skip One2Many Many2Many
                elif ttype in ('many2many', 'one2many'):
                    continue
                # Skip Computed Field
                if not field.store:
                    continue

                if field_name not in field_by_name[table_name]:
                    field = Field.create({
                        'name': title,
                        'field_name': field_name,
                        'field_type': field_type,
                        'field_type_origin': ttype,
                        'table_id': table.id,
                        'foreign_table': foreign_table,
                        'foreign_column': foreign_column,
                    })
                else:
                    field = field_by_name[table_name][field_name]
                    field.write({
                        'name': title,
                        'field_name': field_name,
                        'field_type': field_type,
                        'field_type_origin': ttype,
                        'table_id': table.id,
                        'foreign_table': foreign_table,
                        'foreign_column': foreign_column,
                    })
                    field_by_name[table_name].pop(field_name)

        return {
            'table_by_name': table_by_name,
            'field_by_name': field_by_name
        }
        super(IziDataSourceDBOdoo, self).get_source_tables_db_odoo()