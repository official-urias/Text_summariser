from flask import Flask, request, render_template
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# Ensure you have downloaded the necessary NLTK data files
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/summarize', methods=['POST'])
def summarize():
    if request.method == 'POST':
        # Get text from the form
        text = request.form['text']

        if not text.strip():
            return "Please provide valid text to summarize.", 400

        # Tokenizing the text
        stopWords = set(stopwords.words("english"))
        words = word_tokenize(text)

        # Creating a frequency table
        freqTable = dict()
        for word in words:
            word = word.lower()
            if word in stopWords:
                continue
            if word in freqTable:
                freqTable[word] += 1
            else:
                freqTable[word] = 1

        # Scoring sentences
        sentences = sent_tokenize(text)
        sentenceValue = dict()
        for sentence in sentences:
            for word, freq in freqTable.items():
                if word in sentence.lower():
                    if sentence in sentenceValue:
                        sentenceValue[sentence] += freq
                    else:
                        sentenceValue[sentence] = freq

        # Calculating average sentence value
        sumValues = sum(sentenceValue.values())
        average = int(sumValues / len(sentenceValue)) if sentenceValue else 0

        # Generating summary
        summary = ''
        for sentence in sentences:
            if sentence in sentenceValue and sentenceValue[sentence] > (1.2 * average):
                summary += " " + sentence

        return render_template('result.html', summary=summary)


# HTML templates
@app.route('/templates/<filename>')
def serve_file(filename):
    with open(f'templates/{filename}', 'r') as f:
        return f.read()


if __name__ == '__main__':
    app.run(debug=True)
