import gradio as gr
from doc_search import ES
from model.chatglm_llm import ChatGLM
from configs.params import ModelParams

PROMPT_TEMPLATE = """已知信息：
{context} 

根据上述已知信息，简洁和专业的来回答用户的问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题” 或 “没有提供足够的相关信息”，不允许在答案中添加编造成分，答案请使用中文。 问题是：{question}"""

model_config = ModelParams()
es = ES(model_config.embedding_model)
llm = ChatGLM(model_config.llm_model)


def clear_session():
    return '', [], ''


def search_doc(question, search_method, top_k, knn_boost):
    if search_method == "approximate kNN search":
        result = es.knn_search(question, top_k)
    elif search_method == "hybrid retrieval":
        result = es.hybrid_search(question, top_k, knn_boost)
    else:
        result = es.exact_search(question, top_k)
    return result


def doc_format(doc_list):
    result = ''
    for i in doc_list:
        result += 'source: ' + i['source'] + '\n' + 'score: ' + str(i['score']) + '\n' + 'content: ' + i['content'] + '\n'
    return result


def predict(question, search_method, top_k, max_token, temperature, top_p, knn_boost, history, history_length):
    llm.max_token = max_token
    llm.temperature = temperature
    llm.top_p = top_p
    llm.history_len = history_length
    search_res = search_doc(question, search_method, top_k, knn_boost)
    search_result = doc_format(search_res)

    informed_context = ''
    for i in search_res:
        informed_context += i['content'] + '\n'
    prompt = PROMPT_TEMPLATE.replace("{question}", question).replace("{context}", informed_context)
    for answer_result in llm.generatorAnswer(prompt=prompt, history=history, streaming=True):
        history = answer_result.history
        history[-1][0] = question
        yield history, history, search_result, ""


if __name__ == "__main__":
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("""<h1><center>智能客服 demo</center></h1>""")

        with gr.Row():
            chatbot = gr.Chatbot(scale=2)
            search_out = gr.Textbox(label="SearchResult", interactive=False, scale=1)

        with gr.Row():
            user_input = gr.Textbox(show_label=False, placeholder="Input...", lines=4, container=False, scale=3)
            with gr.Column(scale=1):
                submitBtn = gr.Button("Submit", variant="primary")
                emptyBtn = gr.Button("Clear History")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("""LLM setting""")
                max_length = gr.Slider(0, 32768, value=8192, step=1.0, label="Maximum length", interactive=True)
                top_p = gr.Slider(0, 1, value=0.8, step=0.01, label="Top P", interactive=True)
                temperature = gr.Slider(0, 1, value=0.95, step=0.01, label="Temperature", interactive=True)
                history_length = gr.Slider(0, 10, value=3, step=1, label="history_length", interactive=True)

            with gr.Column(scale=1):
                gr.Markdown("""search setting""")
                with gr.Row():
                    search_method = gr.Radio(['approximate kNN search', 'hybrid retrieval', 'exact kNN'],
                                             value='exact kNN',
                                             label="Search Method")
                    with gr.Column():
                        top_k = gr.Slider(0, 10, value=5, step=1.0, label="top_k", interactive=True)
                        knn_boost = gr.Slider(0, 1, value=0.9, step=0.1, label="knn_boost", interactive=True)
                        file = gr.File(label='请上传知识库文件', file_types=['.txt', '.md', '.docx', '.pdf'])
                        init_vs = gr.Button("ES存储")

        history = gr.State([])

        submitBtn.click(predict,
                        inputs=[user_input, search_method, top_k, max_length, temperature, top_p, knn_boost, history, history_length],
                        outputs=[chatbot, history, search_out, user_input]
                        )
        init_vs.click(
            fn=es.doc_upload,
            show_progress=True,
            inputs=[file],
            outputs=[search_out],
        )

        emptyBtn.click(fn=clear_session, inputs=[], outputs=[chatbot, history, search_out], queue=False)

    demo.queue().launch(share=False, inbrowser=True, server_name="0.0.0.0", server_port=8000)
