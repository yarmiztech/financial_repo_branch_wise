from odoo import fields,models,api,_
from odoo.tests.common import Form
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class FinancialReportBranch(models.Model):
    _name = "financial.repo.branch"
    _order = 'id desc'

    branch_id = fields.Many2one('company.branches',string='Branch Name')
    financial_lines = fields.One2many('financial.repo.lines','financial_repo_id')
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="to Date")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    profit_loss = fields.Float(string='Profit/Loss')
    @api.onchange('from_date', 'to_date','branch_id')
    def _onchange_to_dates(self):
        if self.branch_id:
            profit_loss = 0.0;
            invoices = self.env['account.move'].search(
                [('invoice_date', '<=', self.to_date), ('invoice_date', '>=', self.from_date),
                 ('move_type', '=', 'out_invoice'),('branch_id', '=', self.branch_id.id), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id)])

            list = []
            all = (0, 0, {
                'source': 'Sales',
                'total_value': sum(invoices.mapped('amount_total')),
                # 'tax_amount': sum(invoices.mapped('amount_tax'))

            })
            profit_loss += sum(invoices.mapped('amount_total'))
            list.append(all)
            invoices = self.env['account.move'].search(
                [('invoice_date', '<=', self.to_date), ('invoice_date', '>=', self.from_date),
                 ('move_type', '=', 'out_invoice'), ('branch_id', '=', self.branch_id.id), ('state', '=', 'posted'),
                 ('company_id', '=', self.company_id.id)])
            vat_receivable = (0, 0, {
                'source': 'Vat Receivable',
                'total_value': sum(invoices.mapped('amount_tax'))
            })
            profit_loss += sum(invoices.mapped('amount_tax'))
            list.append(vat_receivable)
            bills = self.env['account.move'].search(
                [('invoice_date', '<=', self.to_date), ('invoice_date', '>=', self.from_date),
                 ('move_type', '=', 'in_invoice'),('branch_id', '=', self.branch_id.id), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id)])

            po_all = (0, 0, {
                'source': 'Purchase',
                'total_value': sum(bills.mapped('amount_total')),
                # 'tax_amount': sum(bills.mapped('amount_tax'))

            })
            list.append(po_all)
            profit_loss -= sum(bills.mapped('amount_total'))
            branch_expenses = self.env['straw.expenses.lines'].search([('payment_date', '<=', self.to_date),('payment_date', '>=', self.from_date),
                ('branch_id', '=', self.branch_id.id)])
            exp_all = (0, 0, {
                'source': 'Expenses',
                'total_value': sum(branch_expenses.mapped('amount')),
                # 'tax_amount': sum(bills.mapped('amount_tax'))

            })
            list.append(exp_all)
            profit_loss -= sum(branch_expenses.mapped('amount'))
            branch_payslips = self.env['branch.payslip'].search([('create_date', '<=', self.to_date),('create_date', '>=', self.from_date),
                            ('branch_id', '=', self.branch_id.id)]).mapped('payslip_ids')
            payslips = (0, 0, {
                'source': 'Salary',
                'total_value': sum(branch_payslips.mapped('total_amount_journal')),
                # 'tax_amount': sum(bills.mapped('amount_tax'))

            })
            list.append(payslips)
            profit_loss -= sum(branch_payslips.mapped('total_amount_journal'))

            bills = self.env['account.move'].search(
                [('invoice_date', '<=', self.to_date), ('invoice_date', '>=', self.from_date),
                 ('move_type', '=', 'in_invoice'),('branch_id', '=', self.branch_id.id), ('state', '=', 'posted'), ('company_id', '=', self.company_id.id)])

            vat_payable = (0, 0, {
                'source': 'Vat Payable',
                'total_value': sum(bills.mapped('amount_tax')),
            })
            list.append(vat_payable)
            profit_loss -= sum(bills.mapped('amount_tax'))
            print('profit_loss',profit_loss)
            vat_payable = (0, 0, {
                'source': 'Profit/Loss',
                'total_value': profit_loss,
            })
            list.append(vat_payable)
            self.financial_lines = False
            self.financial_lines = list



        # self.difference_amount = self.tax_return_lines.filtered(
        #     lambda a: a.source == 'Sales').tax_amount - self.tax_return_lines.filtered(
        #     lambda a: a.source == 'Purchase').tax_amount


class FinancialRepoBranchLines(models.Model):
    _name = "financial.repo.lines"

    financial_repo_id = fields.Many2one('financial.repo.branch')
    source = fields.Char(string="Source")
    total_value = fields.Float(string="Total")




class TaxReturn(models.Model):
    _inherit = "tax.return"
    _order = "id desc"


    def action_payment_done(self):
        vals = {
            'journal_id': self.journal_id.id,
            'state': 'draft',
            'ref': self.name
        }
        pay_id_list = []
        move_id = self.env['account.move'].create(vals)
        label = self.name

        # if self.type_of_credit == False:
        temp = (0, 0, {
            'account_id': self.env['account.account'].sudo().search(
                [('name', '=', 'Vat Receivable'),('company_id','=',self.company_id.id)]).id,
            'name': label,
            'move_id': move_id.id,
            'date': self.create_date,
            # 'partner_id': driver_id.id,
            'credit': self.tax_return_lines.filtered(lambda a:a.source == 'Purchase').tax_amount,
            'debit': 0,

        })
        pay_id_list.append(temp)
        acc = self.journal_id.payment_credit_account_id
        temp = (0, 0, {
            'account_id': acc.id,
            'name': label,
            'move_id': move_id.id,
            'date': self.create_date,
            'debit': 0,
            'credit':self.difference_amount,
        })
        pay_id_list.append(temp)

        acc = self.env['account.account'].sudo().search(
            [('name', '=', 'Sales Tax Payable'),
             ('company_id','=',self.company_id.id)])
        temp = (0, 0, {
            'account_id': acc.id,
            'name': label,
            'move_id': move_id.id,
            'date': self.create_date,
            'credit': 0,
            'debit':self.tax_return_lines.filtered(lambda a:a.source == 'Sales').tax_amount ,
        })
        pay_id_list.append(temp)
        move_id.line_ids = pay_id_list
        self.account_move =move_id
        self.write({'state':'confirm'})
        move_id.action_post()
        pay_id_list = []
        for k in move_id.line_ids:
            pay_id_list.append(k.id)

        if self.env['account.bank.statement'].search([]):
            if self.env['account.bank.statement'].search(
                    [('company_id', '=', self.journal_id.company_id.id),
                     ('journal_id', '=', self.journal_id.id)]):
                bal = self.env['account.bank.statement'].search(
                    [('company_id', '=', self.journal_id.company_id.id),
                     ('journal_id', '=', self.journal_id.id)])[
                    0].balance_end_real
            else:
                bal = 0
        else:
            credit = sum(self.env['account.move.line'].search(
                [('account_id', '=', self.journal_id.payment_credit_account_id.id)]).mapped(
                'debit'))
            debit = sum(self.env['account.move.line'].search(
                [('account_id', '=', self.journal_id.payment_debit_account_id.id)]).mapped(
                'debit'))
            bal = debit - credit
        final = 0
        # if self.partner_type == 'supplier':
        final = bal - self.difference_amount
        # elif self.partner_type == 'customer':
        #     final = bal + self.amount_total
        # else:
        #     final = bal

        stmt = self.env['account.bank.statement'].create({'name': self.journal_id.company_id.partner_id.name,
                                                          'balance_start': bal,
                                                          'journal_id': self.journal_id.id,
                                                          'balance_end_real': final

                                                          })
        payment_list = []
        supplier_amount = 0
        # if self.partner_type == 'supplier':
        supplier_amount = -self.difference_amount
        # else:
        #     supplier_amount = self.amount_total

        product_line = (0, 0, {
            'date': datetime.today().date(),
            'name': self.name,
            'partner_id': self.company_id.partner_id.id,
            'payment_ref': self.name,
            'amount': supplier_amount
        })
        payment_list.append(product_line)
        if stmt:
            stmt.line_ids = payment_list
            unwanted_move = stmt.move_line_ids.mapped('move_id')
            stmt.stmt_ref_lines = payment_list
            unwanted_move.unlink()
            stmt.write({'state':'confirm'})





