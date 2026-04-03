import re

def load_rubric(file_path="rubric.txt"):
    with open(file_path, "r") as f:
        content = f.read()
    
    # Parse rubric (simple parsing)
    rubric = {
        "correctness": {"executes": 20, "results": 20},
        "performance": {"fast": 15, "medium": 10, "slow": 5},
        "optimization": {"indexes": 10, "operations": 10},
        "style": {"syntax": 5, "naming": 5},
        "feedback": {}
    }
    
    # Extract feedback guidelines
    feedback_match = re.search(r'Feedback Guidelines:(.*)', content, re.DOTALL)
    if feedback_match:
        rubric["feedback"] = feedback_match.group(1).strip()
    
    return rubric

def calculate_score(is_valid, exec_time, query_plan, rubric):
    score = 0
    
    # Correctness
    if is_valid:
        score += rubric["correctness"]["executes"] + rubric["correctness"]["results"]
    
    # Performance
    if exec_time < 1:
        score += rubric["performance"]["fast"]
    elif exec_time < 5:
        score += rubric["performance"]["medium"]
    else:
        score += rubric["performance"]["slow"]
    
    # Optimization (simplified)
    if "index" in query_plan.lower():
        score += rubric["optimization"]["indexes"]
    score += rubric["optimization"]["operations"]  # Assume for now
    
    # Style (assume full for now)
    score += rubric["style"]["syntax"] + rubric["style"]["naming"]
    
    return min(score, 100)

def generate_feedback(is_valid, exec_time, query_plan, rubric):
    feedback = rubric["feedback"]
    if not is_valid:
        feedback += " Query failed to execute."
    if exec_time > 5:
        feedback += " Performance is poor."
    return feedback