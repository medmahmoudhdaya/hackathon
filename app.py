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
app.secret_key = "supersecretkey"  # Required for flashing messages

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

def generate_snack_ideas(ingredients, goal=None):
    try:
        # System role to guide the AI
        system_prompt = (
            "أنت أخصائي تغذية متخصص في المأكولات العربية. قم بإنشاء أفكار لوجبات خفيفة صحية بناءً على المكونات المقدمة. "
            "يمكنك إضافة أي مكونات إضافية لتحسين الوجبة الخفيفة، سواء من ناحية النكهة أو القيمة الغذائية أو المظهر. "
            "يجب أن تكون الوجبات الخفيفة سهلة التحضير وتحتوي على خطوات مفصلة. تأكد من أن التعليمات واضحة ومكتوبة باللغة العربية فقط."
        )

        # User role with the specific prompt
        user_prompt = (
            f"قم بإنشاء أفكار لوجبات خفيفة صحية باللغة العربية، مع تضمين خطوات مفصلة حول كيفية تحضير كل وجبة، بناءً على المكونات التالية: {', '.join(ingredients)}. "
            "يمكنك إضافة أي مكونات إضافية لتحسين الوجبة الخفيفة."
        )
        if goal:
            user_prompt += f" مع الهدف التالي: {goal}."

        completion = client.chat.completions.create(
            model="mistral-saba-24b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
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
        return ["فشل في توليد أفكار للوجبات الخفيفة. يرجى المحاولة مرة أخرى."]

# Helper function to structure the snack ideas
def structure_snack_ideas(snack_ideas):
    structured_ideas = []
    current_idea = {"title": "", "steps": []}

    for line in snack_ideas:
        if line.strip() == "":
            continue  # Skip empty lines
        if ":" in line and not line.startswith("-"):  # Detect a new snack idea title
            if current_idea["title"]:  # Save the previous idea if it exists
                structured_ideas.append(current_idea)
            current_idea = {"title": line.strip(), "steps": []}
        elif line.startswith("-"):  # Detect a step
            current_idea["steps"].append(line.strip())
    
    if current_idea["title"]:  # Add the last idea
        structured_ideas.append(current_idea)
    
    return structured_ideas

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ingredients = request.form.get("ingredients")
        goal = request.form.get("goal")
        
        # Split ingredients into a list
        ingredients_list = [ingredient.strip() for ingredient in ingredients.split(",")]
        
        # Call the AI function to generate snack ideas
        snack_ideas = generate_snack_ideas(ingredients_list, goal)
        
        # Structure the snack ideas for better display
        structured_ideas = structure_snack_ideas(snack_ideas)
        
        # Save the generated snacks to the database and assign IDs
        saved_snacks = []
        for idea in structured_ideas:
            new_snack = Snack(
                ingredients=", ".join(ingredients_list),
                goal=goal,
                name=idea["title"],
                description="\n".join(idea["steps"])
            )
            db.session.add(new_snack)
            db.session.commit()
            saved_snacks.append({
                "id": new_snack.id,
                "title": idea["title"],
                "description": "\n".join(idea["steps"]),
                "steps": idea["steps"],
                "created_at": new_snack.created_at.strftime('%Y-%m-%d')  # Add creation date
            })
        
        # Render the template with the results
        return render_template("index.html", structured_ideas=saved_snacks, show_results=True)
    
    # Fetch saved snacks for the sidebar
    saved_snacks = DietPlan.query.join(Snack).order_by(DietPlan.created_at.desc()).all()
    snacks_data = []

    for plan in saved_snacks:
        snacks_data.append({
            "id": plan.snack.id,
            "title": plan.snack.name,
            "date": plan.created_at.strftime('%Y-%m-%d')  # Format the date
        })
    
    # Render the template without results for GET requests
    return render_template("index.html", show_results=False, saved_snacks=snacks_data)

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
            flash("تم حفظ الوجبة الخفيفة بنجاح!", "message")
        else:
            flash("هذه الوجبة موجودة بالفعل في خطتك الغذائية.", "warning")
    return redirect(url_for("index"))

@app.route("/remove_from_plan/<int:diet_plan_id>", methods=["POST"])
def remove_from_plan(diet_plan_id):
    diet_plan = DietPlan.query.get_or_404(diet_plan_id)
    db.session.delete(diet_plan)
    db.session.commit()
    flash("تم حذف الوجبة الخفيفة من خطتك الغذائية.", "success")
    return redirect(url_for("my_diet_plan"))

@app.route("/snack/<int:snack_id>")
def snack_details(snack_id):
    # Fetch the snack from the database
    snack = Snack.query.get_or_404(snack_id)
    return render_template("snack_details.html", snack=snack)

# Create the database and tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)