from flask import Flask, render_template, request, session
import google.generativeai as genai
import os
import re  # Import regex for better parsing

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session

# Load API key from environment
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Quiz page route
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        user_prompt = request.form.get('prompt', '')
        timer = int(request.form.get('timer', 30))
        difficulty = request.form.get('difficulty', 'medium')
        num_questions = int(request.form.get('num_questions', 5))
        topic = request.form.get('topic', 'general')

        # Create a GenerativeModel instance and generate quiz content
        model = genai.GenerativeModel('gemini-1.5-flash')

        try:
            # Improved prompt structure
            specific_details = user_prompt  # This could include details like a specific era, key figures, etc.
            response = model.generate_content(
                f"Generate {num_questions} multiple choice questions about {topic}, specifically focusing on {specific_details}. The difficulty should be {difficulty}. Each question must have 4 options labeled A), B), C), and D)."
            )

            # Print out the raw response from the model for debugging
            print("Raw Model Response:", response.text)

            # Process the response as before
            lines = response.text.strip().split('\n')
            generated_quiz = []
            current_question = None

            for line in lines:
                line = line.strip()
                question_match = re.match(r"^\*\*(\d+)\.\s*(.*?)\*\*$", line)
                if question_match:
                    current_question = {"question": question_match.group(2), "options": []}
                    generated_quiz.append(current_question)
                elif line.startswith(("A)", "B)", "C)", "D)")):
                    if current_question is not None:
                        current_question["options"].append(line)

            # Filter out invalid questions (questions without exactly 4 options)
            generated_quiz = [q for q in generated_quiz if len(q['options']) == 4]

            if not generated_quiz:
                raise Exception("No valid questions generated. Try again.")

            # Store questions in session
            session['quiz'] = generated_quiz
            session['current_question'] = 0
            session['user_answers'] = []
            session['timer'] = timer

            return render_template('quiz.html', quiz_generated=True, current_question=session['current_question'], timer=session['timer'], question=session['quiz'][0])

        except Exception as e:
            return render_template('quiz.html', quiz_generated=False, error=str(e))

    return render_template('quiz.html', quiz_generated=False)


# Submit answers and proceed to the next question
@app.route('/next_question', methods=['POST'])
def next_question():
    user_answer = request.form.get('user_answer')
    session['user_answers'].append(user_answer)
    session['current_question'] += 1

    # Check if there are more questions
    if session['current_question'] < len(session['quiz']):
        return render_template('quiz.html', quiz_generated=True, current_question=session['current_question'], timer=session['timer'], question=session['quiz'][session['current_question']])
    else:
        return render_template('results.html', answers=session['user_answers'], quiz=session['quiz'])

# News page route (Removed duplicate route, retained the one with POST functionality)
@app.route('/news', methods=['GET', 'POST'])
def news_page():
    if request.method == 'POST':
        news_prompt = request.form.get('news_prompt', 'student news')

        # Generate or fetch news content (replace this with actual news API if available)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"Provide the latest {news_prompt}")

        # Example of splitting response into articles (modify as per actual API response format)
        generated_articles = response.text.split('\n\n')  # Assuming new articles are separated by double newlines
        news_articles = []
        for article in generated_articles:
            lines = article.split('\n')
            if len(lines) >= 2:
                news_articles.append({
                    'title': lines[0],
                    'description': lines[1],
                    'thumbnail_url': 'https://via.placeholder.com/300x180.png?text=Thumbnail',  # Example thumbnail URL
                    'url': '#',  # Replace with actual URL if available
                })

        # Store in session to allow reloading more articles
        session['news_articles'] = news_articles
    else:
        # Load from session if already generated
        news_articles = session.get('news_articles', [])

    return render_template('news.html', news_articles=news_articles)

@app.route('/review', methods=['GET', 'POST'])
def review():
    if request.method == 'POST':
        topic_prompt = request.form.get('topic_prompt', '')
        model = genai.GenerativeModel('gemini-1.5-flash')

        try:
            # Generate relevant information
            response_info = model.generate_content(f"Provide detailed information about {topic_prompt}.")
            review_info = response_info.text.strip()

            # Generate YouTube links
            response_youtube = model.generate_content(f"Generate YouTube links related to {topic_prompt}.")
            youtube_links = response_youtube.text.strip().split('\n')

            return render_template('review.html', review_generated=True, review_info=review_info, youtube_links=youtube_links)

        except Exception as e:
            return render_template('review.html', review_generated=False, error=str(e))

    return render_template('review.html', review_generated=False)


# Code page route
@app.route('/code')
def code():
    return render_template('code.html')


if __name__ == '__main__':
    app.run(debug=True)
