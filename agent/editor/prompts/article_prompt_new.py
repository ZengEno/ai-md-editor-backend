from ...agent_classes import Article, HighlightData


def highlight_prompt(article: Article, highlight_data: HighlightData):
    if not highlight_data.text:
        return "The user has not highlighted any text."
    else:
        lines = article.content.split('\n')
        content_around_highlight = ""
        for i in range(highlight_data.start_line-1, highlight_data.end_line):
            content_around_highlight += f"<line_{i+1}>{lines[i]}</line_{i+1}>\n"

        return f'''The user has highlighted or selected the following text in the current article:
<highlighted_text>
{highlight_data.text}
</highlighted_text>

The highlighted or selected text belongs to the following article content:
<content_around_highlight>
{content_around_highlight}
</content_around_highlight>

You should use the highlighted text as context when generating your response.
'''


def current_article_prompt(article: Article, highlight_data: HighlightData):
    if not article.content:
        return "The user has not written anything yet."
    else:
        lines = article.content.split('\n')
        formatted_article_by_lines = ""
        for i, line in enumerate(lines):
            formatted_article_by_lines += f"<line_{i+1}>{line}</line_{i+1}>\n"

        return f'''Below is the file name of the article the user is currently working on:
<current_article_file_name>
{article.file_name}
</current_article_file_name>
        
Below is the article content the user is working on, be aware that each line is wrapped in <line_i> tags.
<current_article_content>
{formatted_article_by_lines}
</current_article_content>

{highlight_prompt(article, highlight_data)}
'''


def other_articles_prompt(other_articles: list[Article]):
    if not other_articles:
        return ""
    else:
        other_articles_str = ""
        for i, article in enumerate(other_articles):
            other_articles_str += f"<Other_Article_Number_{i+1}>\n"
            other_articles_str += f"Article File Name: {article.file_name}\nContent: {article.content}\n"
            other_articles_str += f"</Other_Article_Number_{i+1}>\n\n"

        return f'''The user has written other articles in the past, you can use these articles as context.
There may be multiple other articles, each has a file name and content:
<other_articles>
{other_articles_str}
</other_articles>

You should use these other articles as context when responding to the users question, but the current article is the most important.
'''


def reference_articles_prompt(reference_articles: list[Article]):
    if not reference_articles:
        return ""
    else:
        reference_articles_str = ""
        for i, article in enumerate(reference_articles):
            reference_articles_str += f"<Reference_Article_Number_{i+1}>\n"
            reference_articles_str += f"Article File Name: {article.file_name}\nContent: {article.content}\n"
            reference_articles_str += f"</Reference_Article_Number_{i+1}>\n\n"

        return f'''The user has the following reference articles they want to use as context when generating response, there may be multiple articles, each has a file name and content:
<reference_articles>
{reference_articles_str}
</reference_articles>

You should use these reference articles as context when responding to the users question, but the current article is the most important.
'''