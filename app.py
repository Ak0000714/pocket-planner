from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:karuna%40123@localhost/expenses_tracker'
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define Expense and Budget models
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget = db.Column(db.Float, nullable=False)

@app.route('/')
def index():
    try:
        page = request.args.get('page', 1, type=int)
        expenses = Expense.query.paginate(page=page, per_page=10, error_out=False)
        categories = [category[0] for category in db.session.query(Expense.category).distinct().all()]

        budget_entry = Budget.query.first()
        budget = budget_entry.budget if budget_entry else 0

        total_expenses = sum(expense.amount for expense in expenses.items)
        balance = budget - total_expenses

        # Prepare data for charts (Category and Monthly Expenses)
        category_expenses = []
        for category in categories:
            category_expenses.append(
                sum(expense.amount for expense in Expense.query.filter_by(category=category).all())
            )

        monthly_expenses = {}
        for expense in Expense.query.all():
            month = expense.date.strftime('%B')
            if month in monthly_expenses:
                monthly_expenses[month] += expense.amount
            else:
                monthly_expenses[month] = expense.amount

        # Prepare labels and values for the chart
        monthly_expenses_data = {'labels': list(monthly_expenses.keys()), 'values': list(monthly_expenses.values())}

        return render_template(
            'index.html', total_expenses=total_expenses, balance=balance, budget=budget,
            categories=categories, expenses=expenses, category_expenses=category_expenses,
            monthly_expenses=monthly_expenses_data
        )

    except Exception as e:
        flash("An error occurred. Please try again.", 'error')
        return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_expense():
    print("gwejhf")
    try:
        category = request.form['category']
        amount = request.form['amount']
        description = request.form.get('description', '')
        date = request.form['date']

        if not amount.replace('.', '', 1).isdigit() or float(amount) <= 0:
            flash("Invalid amount.", 'error')
            return redirect(url_for('index'))

        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", 'error')
            return redirect(url_for('index'))

        new_expense = Expense(category=category, amount=float(amount), description=description, date=date)
        db.session.add(new_expense)
        db.session.commit()

        # Fetch the current budget and total expenses after adding the new expense
        budget_entry = Budget.query.first()
        budget = budget_entry.budget if budget_entry else 0
        total_expenses = sum(expense.amount for expense in Expense.query.all())
        
        # Check if the expenses exceed the budget
        if total_expenses > budget:
            flash(f"Warning: Your expenses have exceeded your budget by ₹{total_expenses - budget}.", 'warning')
        else:
            flash('Expense added successfully!')

    except Exception as e:
        flash("An error occurred while adding the expense.", 'error')

    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_expense(id):
    try:
        expense_to_delete = Expense.query.get(id)
        if expense_to_delete:
            db.session.delete(expense_to_delete)
            db.session.commit()
            flash('Expense deleted successfully!')
        else:
            flash('Expense not found.', 'error')

    except Exception as e:
        flash("An error occurred while deleting the expense.", 'error')

    return redirect(url_for('index'))

@app.route('/update_budget', methods=['POST'])
def update_budget():
    try:
        # Get the new budget value from the form
        new_budget = request.form['budget']
        
        # Validate the new budget value
        if not new_budget.replace('.', '', 1).isdigit() or float(new_budget) < 0:
            flash("Invalid budget amount.", 'error')
            return redirect(url_for('index'))

        # Check if a budget already exists
        budget_entry = Budget.query.first()
        
        # If a budget exists, update it; otherwise, create a new budget entry
        if budget_entry:
            budget_entry.budget = float(new_budget)
            db.session.commit()  # Make sure to commit changes
            flash('Budget updated successfully!')
        else:
            # No existing budget, so create a new one
            new_budget_entry = Budget(budget=float(new_budget))
            db.session.add(new_budget_entry)
            db.session.commit()  # Commit the new entry
            flash('Budget created successfully!')

    except Exception as e:
        flash(f"An error occurred while updating the budget: {str(e)}", 'error')

    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
