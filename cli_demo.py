from configs.model_config import *
from chains.local_doc_qa import LocalDocQA
import os
import nltk
from models.loader.args import parser
import models.shared as shared
from models.loader import LoaderCheckPoint
nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path
import datetime
import json
# Show reply with source text from input document
REPLY_WITH_SOURCE = True


def preprocess_questions(input_file):
    questions_data=[]
    with open(input_file, 'r') as fp:
        querys=json.load(fp)
    for query in querys:
        id = query['id']
        content = query['content']
        questions = query['questions']
        for q in questions:
            tmp={'id':id, 'content': content, 'question': q}
            questions_data.append(tmp)
    return questions_data

def main():

    llm_model_ins = shared.loaderLLM(use_ptuning_v2=USE_PTUNING_V2)
    llm_model_ins.history_len = LLM_HISTORY_LEN

    local_doc_qa = LocalDocQA()
    local_doc_qa.init_cfg(llm_model=llm_model_ins,
                          embedding_model=EMBEDDING_MODEL,
                          embedding_device=EMBEDDING_DEVICE,
                          top_k=VECTOR_SEARCH_TOP_K)
    vs_path = "/home/cambricon/lsc/data/datasets/knowledge_point_modify_rmhtmllatex_keepchinese_0728_FAISS_20230816_082934/vector_store"
    # vs_path = None
    while not vs_path:
       print("注意输入的路径是完整的文件路径，例如knowledge_base/`knowledge_base_id`/content/file.md，多个路径用英文逗号分割")
       #filepath = input("Input your local knowledge file path 请输入本地知识文件路径：")
       filepath = "/home/cambricon/lsc/data/datasets/knowledge_point_modify_rmhtmllatex_keepchinese_0728.csv"
       #filepath = "/home/cambricon/lsc/data/datasets/difficult_ques_modify_keepchinese.csv"
       #filepath = "/workspace/data/datasets/knowledge_point_modify.csv"
       #filepath = "/workspace/data/datasets/2023-07-10-11-50-34_EXPORT_CSV_9734122_741_knowledge_point_card_0.csv"
       # 判断 filepath 是否为空，如果为空的话，重新让用户输入,防止用户误触回车
       if not filepath:
           continue

       # 支持加载多个文件
       filepath = filepath.split(",")
       # filepath错误的返回为None, 如果直接用原先的vs_path,_ = local_doc_qa.init_knowledge_vector_store(filepath)
       # 会直接导致TypeError: cannot unpack non-iterable NoneType object而使得程序直接退出
       # 因此需要先加一层判断，保证程序能继续运行
       temp,loaded_files = local_doc_qa.init_knowledge_vector_store(filepath)
       if temp is not None:
           vs_path = temp
           # 如果loaded_files和len(filepath)不一致，则说明部分文件没有加载成功
           # 如果是路径错误，则应该支持重新加载
           if len(loaded_files) != len(filepath):
               reload_flag = eval(input("部分文件加载失败，若提示路径不存在，可重新加载，是否重新加载，输入True或False: "))
               if reload_flag:
                   vs_path = None
                   continue

           print(f"the loaded vs_path is 加载的vs_path为: {vs_path}")
       else:
           print("load file failed, re-input your local knowledge file path 请重新输入本地知识文件路径")
    #fp = open('test_questions.txt')
    #questions = fp.readlines()
    #print(questions)
    # fp.close()
    history = []
    # fp = open('query1.4MB_top1_0.json', 'w')
    # results=[]
    questions = preprocess_questions('query1.4MB.json')
    # while True:
    # for idx, question in enumerate(questions):
    while True:
        query = input("Input your question 请输入问题：")
        # result.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "  id:" + str(idx) + " " + query)
        question = {'id':0, 'question':query}
        last_print_len = 0
        for resp, history in local_doc_qa.get_knowledge_based_answer(query=query,
                                                                     vs_path=vs_path,
                                                                     chat_history=history,
                                                                     streaming=STREAMING):
            if STREAMING:
                print(resp["result"][last_print_len:], end="", flush=True)
                last_print_len = len(resp["result"])

        # result.write(resp["result"])
        # res = {'id':question['id'], 'content': question['content'],'query': question['question'], 'prompt':resp["prompt"]}
        # results.append(res)

        if REPLY_WITH_SOURCE:
            #source_text = [f"""出处 [{inum + 1}] {os.path.split(doc.metadata['source'])[-1]}：\n\n{doc.page_content}\n\n"""
            source_text = [f"""\n出处 [{inum + 1}] {os.path.split(doc[0].metadata['source'])[-1]}: row {doc[0].metadata['row']}\n{doc[0].page_content}\n相关度：{doc[1]}"""
                           # f"""相关度：{doc.metadata['score']}\n\n"""
                           for inum, doc in
                           enumerate(resp["source_documents"])]
            related_text = "\n" + "\n".join(source_text)
            print(related_text)
            # result.write(related_text)
            # result.write('\n====================================================\n\n\n')
    # json.dump(results, fp, ensure_ascii=False, indent=4)
    # fp.close()


if __name__ == "__main__":
#     # 通过cli.py调用cli_demo时需要在cli.py里初始化模型，否则会报错：
    # langchain-ChatGLM: error: unrecognized arguments: start cli
    # 为此需要先将
    # args = None
    # args = parser.parse_args()
    # args_dict = vars(args)
    # shared.loaderCheckPoint = LoaderCheckPoint(args_dict)
    # 语句从main函数里取出放到函数外部
    # 然后在cli.py里初始化
    args = None
    args = parser.parse_args()
    args_dict = vars(args)
    shared.loaderCheckPoint = LoaderCheckPoint(args_dict)
    main()
