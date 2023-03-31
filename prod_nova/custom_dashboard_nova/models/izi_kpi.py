from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.safe_eval import safe_eval

class IziKPI (models.Model):
    _inherit = 'izi.kpi'
    
    def action_calculate_value(self):
        self.ensure_one()
        kpi_data_by_period = {}
        # Run Calculation On Child KPI First
        child_kpi_datas = []
        for child in self.child_ids:
            child_kpi_data_by_period = child.action_calculate_value()
            child_kpi_datas.append(child_kpi_data_by_period)
        # Get Values & Target By Child KPIs
        if self.child_ids and self.summarize_childs:
            for ckd_by_period in child_kpi_datas:
                for period in self.period_ids:
                    if period.id in ckd_by_period:
                        if period.id not in kpi_data_by_period:
                            kpi_data_by_period[period.id] = {}
                        child_lines_by_name = ckd_by_period[period.id]
                        for line_name in child_lines_by_name:
                            if line_name not in kpi_data_by_period[period.id]:
                                kpi_data_by_period[period.id][line_name] = {
                                    'kpi_id': self.id,
                                    'period_id': period.id,
                                    'name': line_name,
                                    'date': child_lines_by_name[line_name].date,
                                    'interval': self.interval,
                                    'achievement': 0,
                                    'target': 0,
                                    'value': 0,
                                }
                            kpi_data_by_period[period.id][line_name]['target'] += child_lines_by_name[line_name].target
                            kpi_data_by_period[period.id][line_name]['value'] += child_lines_by_name[line_name].value
            # Create Line
            self.line_ids.unlink()
            for period_id in kpi_data_by_period:
                for line_name in kpi_data_by_period[period_id]:
                    total_target = kpi_data_by_period[period_id][line_name]['target']
                    total_value = kpi_data_by_period[period_id][line_name]['value']
                    total_achievement = 0
                    if total_target != 0:
                        total_achievement = 100 * total_value / total_target
                    kpi_data_by_period[period_id][line_name]['achievement'] = total_achievement
                    new_line = self.env['izi.kpi.line'].create(kpi_data_by_period[period_id][line_name])
                    kpi_data_by_period[period_id][line_name] = new_line
            return kpi_data_by_period

        # If Not Summarize By Child KPIs
        data_by_group_key = {}
        # ORM Model Calculation
        if self.calculation_method == 'model':
            domain = []
            measurements = []
            groups = []
            group_key = ''
            if self.measurement_field_id and self.date_field_id and self.interval:
                if self.domain:
                    domain = safe_eval(self.domain)
                measurements = ['measurement:sum(%s)' % self.measurement_field_id.field_name]
                group_key = '%s:%s' % (self.date_field_id.field_name, self.interval)
                groups = [group_key]
            else:
                raise UserError('Please input measurement, date field and interval first.') 

            res_data = self.env[self.model_id.model].read_group(domain, measurements, groups, lazy=False)
            for rd in res_data:
                if rd[group_key] not in data_by_group_key:
                    traducir = {'enero':'January','febrero':'February','marzo':'March','abril':'April','mayo':'May','junio':'June','julio':'July','agosto':'August','septiembre':'September','octubre':'Octber','noviembre':'November','diciembre':'December',
                                'ene':'Jan','feb':'Feb','mar':'Mar','abr':'Apr','may':'May','jun':'Jun','jul':'Jul','ago':'Aug','sep':'Sep','oct':'Oct','nov':'Nov','dic':'Dic'}
                    result = rd[group_key]
                    for ind in traducir:
                        result = result.replace(ind, traducir[ind])
                    data_by_group_key[result] = rd['measurement']
            
        
        # Generate Line
        for period in self.period_ids:
            start_date = period.start_date
            end_date = period.end_date
            interval_start_date = False
            interval_end_date = False
            interval_delta = False
            if self.interval == 'day':
                interval_start_date = start_date
                interval_end_date = end_date
                interval_delta = timedelta(days=1)
                interval_dateformat = '%d %b %Y'
            elif self.interval == 'week':
                interval_start_date = start_date - timedelta(days=start_date.weekday())
                if interval_start_date.year < period.start_date.year:
                    interval_start_date = interval_start_date + timedelta(days=7)
                interval_end_date = end_date - timedelta(days=end_date.weekday())
                interval_delta = timedelta(days=7)
                interval_dateformat = 'W%W %Y'
            elif self.interval == 'month':
                interval_start_date = start_date.replace(day=1)
                interval_end_date = end_date.replace(day=1)
                interval_delta = relativedelta(months=1)
                interval_dateformat = '%B %Y'
            elif self.interval == 'year':
                interval_start_date = start_date.replace(day=1, month=1)
                interval_end_date = end_date.replace(day=1, month=1)
                interval_delta = relativedelta(years=1)
                interval_dateformat = '%Y'
                
            # Check Period Lines
            period_lines_by_name = {}
            for line in self.line_ids:
                # Delete Line With Different Period
                if line.period_id.id not in self.period_ids.ids:
                    line.unlink()
                    continue
                if line.period_id.id == period.id:
                    # Delete Line With Different Interval
                    if line.interval != self.interval or line.date < period.start_date or line.date > period.end_date:
                        line.unlink()
                        continue
                    period_lines_by_name[line.name] = line
                    
            
            if interval_start_date and interval_end_date and interval_delta:
                cur_date = interval_start_date
                while cur_date <= interval_end_date:
                    cur_name = cur_date.strftime(interval_dateformat).replace('W0', 'W')
                    measurement_value = 0
                    if self.calculation_method == 'model' and cur_name in data_by_group_key: 
                        measurement_value = data_by_group_key[cur_name]
                    if self.calculation_method == 'manual' and cur_name in period_lines_by_name:
                        measurement_value = period_lines_by_name[cur_name].value
                    # Check Period Line With The Same Name
                    if cur_name in period_lines_by_name:
                        target = period_lines_by_name[cur_name].target
                        achievement = 0
                        if target != 0:
                            achievement = 100 * measurement_value / target
                        period_lines_by_name[cur_name].write({
                            'value': measurement_value,
                            'achievement': achievement,
                        })
                    else:
                        line_values = {
                            'kpi_id': self.id,
                            'period_id': period.id,
                            'name': cur_name,
                            'date': cur_date,
                            'target': 0,
                            'value': measurement_value,
                            'interval': self.interval,
                            'achievement': 0,
                        }
                        new_line = self.env['izi.kpi.line'].create(line_values)
                        period_lines_by_name[cur_name] = new_line
                    cur_date += interval_delta
            if period.id not in kpi_data_by_period:
                kpi_data_by_period[period.id] = period_lines_by_name
        return kpi_data_by_period
        super(IziKPI, self).action_calculate_value()