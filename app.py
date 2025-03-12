from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from groq import Groq
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diet_plan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Snack model
class Snack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingredients = db.Column(db.String(500), nullable=False)
    goal = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Snack {self.name}>"

# Define the DietPlan model
class DietPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    snack_id = db.Column(db.Integer, db.ForeignKey('snack.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    snack = db.relationship('Snack', backref='diet_plans')

    def __repr__(self):
        return f"<DietPlan {self.snack.name}>"

# Initialize Groq client
groq_api_key = os.getenv('GROQ_API_KEY')
client = Groq(api_key=groq_api_key)

# AI function to generate snack ideas using Groq API
def generate_snack_ideas(ingredients, goal=None):
    try:
        prompt = f"Generate healthy snack ideas based on the following ingredients: {', '.join(ingredients)}"
        if goal:
            prompt += f" with the goal of {goal}."
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        # Extract the content from the completion
        snack_ideas = completion.choices[0].message.content.split("\n")
        return snack_ideas
    except Exception as e:
        print(f"Error generating snack ideas: {e}")
        return ["Failed to generate snack ideas. Please try again."]

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ingredients = request.form["ingredients"].split(", ")
        goal = request.form.get("goal")
        snack_ideas = generate_snack_ideas(ingredients, goal)
        
        # Save the generated snacks to the database
        for idea in snack_ideas:
            if idea.strip():  # Skip empty lines
                snack = Snack(
                    ingredients=", ".join(ingredients),
                    goal=goal,
                    name=idea.split(":")[0].strip() if ":" in idea else idea.strip(),
                    description=idea.split(":")[1].strip() if ":" in idea else idea.strip(),
                )
                db.session.add(snack)
        db.session.commit()

        return render_template("index.html", snack_ideas=snack_ideas, goal=goal, ingredients=ingredients)

    return render_template("index.html", snack_ideas=None)

@app.route("/my_diet_plan")
def my_diet_plan():
    # Fetch all saved snacks from the diet plan
    diet_plans = DietPlan.query.order_by(DietPlan.created_at.desc()).all()
    return render_template("diet_plan.html", diet_plans=diet_plans)

@app.route("/add_to_plan", methods=["POST"])
def add_to_plan():
    snack_id = request.form.get("snack_id")
    if snack_id:
        # Check if the snack is already in the diet plan
        existing_entry = DietPlan.query.filter_by(snack_id=snack_id).first()
        if not existing_entry:
            # Add the snack to the diet plan
            new_entry = DietPlan(snack_id=snack_id)
            db.session.add(new_entry)
            db.session.commit()
            flash("Snack added to your Diet Plan!", "success")
        else:
            flash("This snack is already in your Diet Plan.", "warning")
    return redirect(url_for("my_diet_plan"))

@app.route("/remove_from_plan/<int:diet_plan_id>", methods=["POST"])
def remove_from_plan(diet_plan_id):
    diet_plan = DietPlan.query.get_or_404(diet_plan_id)
    db.session.delete(diet_plan)
    db.session.commit()
    flash("Snack removed from your Diet Plan.", "success")
    return redirect(url_for("my_diet_plan"))

# Create the database and tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.secret_key = "supersecretkey"  # Required for flashing messages
    app.run(debug=True)