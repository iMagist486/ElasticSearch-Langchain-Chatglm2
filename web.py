import re
import gradio as gr
from doc_search import ES
from model.chatglm_llm import ChatLLM
from configs.params import ModelParams

PROMPT_TEMPLATE = """已知信息：
{context} 

根据上述已知信息，简洁和专业的来回答用户的问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题” 或 “没有提供足够的相关信息”，不允许在答案中添加编造成分，答案请使用中文。 问题是：{question}"""

model_config = ModelParams()
es = ES(model_config.embedding_model)
llm = ChatLLM()
llm.load_llm()


def clear_session():
    return '', [], ''


def search_doc(question, search_method, top_k, knn_boost, threshold):
    res = es.doc_search(method=search_method, query=question, top_k=top_k, knn_boost=knn_boost)
    if threshold > 0:
        result = [i for i in res if i['score'] > threshold]
    else:
        result = res
    return result


def doc_format(doc_list):
    result = ''
    for i in doc_list:
        source = re.sub('data/', '', i['source'])
        result += f"source: {source}\nscore: {i['score']}\ncontent: {i['content']}\n"
    return result


def predict(question, search_method, top_k, max_token, temperature, top_p, knn_boost, history, history_length,
            threshold):
    llm.max_token = max_token
    llm.temperature = temperature
    llm.top_p = top_p
    llm.history_len = history_length
    search_res = search_doc(question, search_method, top_k, knn_boost, threshold)
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
    title = """
    # Elasticsearch + ChatGLM demo
    [https://github.com/iMagist486/ElasticSearch-Langchain-Chatglm2](https://github.com/iMagist486/ElasticSearch-Langchain-Chatglm2)
    """
    with gr.Blocks() as demo:
        gr.Markdown(title)

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot()
                user_input = gr.Textbox(show_label=False, placeholder="Input...", lines=4, container=False)
                with gr.Row():
                    submitBtn = gr.Button("Submit", variant="primary")
                    emptyBtn = gr.Button("Clear History")
            search_out = gr.Textbox(label="文档交互", lines=25, max_lines=25, interactive=False, scale=1)

        with gr.Row(variant='compact'):
            with gr.Column():
                gr.Markdown("""LLM设置""")
                max_length = gr.Slider(0, 32768, value=8192, step=1.0, label="Maximum length", interactive=True)
                top_p = gr.Slider(0, 1, value=0.8, step=0.01, label="Top P", interactive=True)
                temperature = gr.Slider(0, 1, value=0.01, step=0.01, label="Temperature", interactive=True)
                history_length = gr.Slider(0, 10, value=3, step=1, label="history_length", interactive=True)

            with gr.Column():
                gr.Markdown("""查询设置""")
                search_method = gr.Radio(['近似查询', '混合查询', '精确查询'],
                                         value='精确查询',
                                         label="Search Method")
                threshold = gr.Number(label="查询阈值(0为不设限)", value=0.00, interactive=True)
                top_k = gr.Slider(0, 10, value=3, step=1.0, label="top_k", interactive=True)
                knn_boost = gr.Slider(0, 1, value=0.5, step=0.1, label="knn_boost", interactive=True)

            with gr.Column():
                gr.Markdown("""知识库管理""")
                file = gr.File(label='请上传知识库文件', file_types=['.txt', '.md', '.doc', '.docx'])
                chunk_size = gr.Number(label="chunk_size", value=300, interactive=True)
                chunk_overlap = gr.Number(label="chunk_overlap", value=10, interactive=True)
                doc_upload = gr.Button("ES存储")

        history = gr.State([])

        submitBtn.click(predict,
                        inputs=[user_input, search_method, top_k, max_length, temperature, top_p, knn_boost, history,
                                history_length, threshold],
                        outputs=[chatbot, history, search_out, user_input]
                        )
        doc_upload.click(
            fn=es.doc_upload,
            show_progress=True,
            inputs=[file, chunk_size, chunk_overlap],
            outputs=[search_out],
        )

        emptyBtn.click(fn=clear_session, inputs=[], outputs=[chatbot, history, search_out], queue=False)

    demo.queue().launch(share=False, inbrowser=True, server_name="0.0.0.0", server_port=8000)
