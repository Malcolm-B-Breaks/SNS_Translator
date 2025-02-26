import re
import yaml
import pandas as pd
from langchain_core.messages import SystemMessage, HumanMessage


def post_translator(language, model, previous_data=None):
    error_counter = 0

    if model == "axios":
        from ai_models.axios_init import axios as agent
    elif model == "veritas":
        from ai_models.veritas_init import veritas as agent
    elif model == "chatGPT4" or model == "chatGPT4_bb":
        from ai_models.chatgpt_init import openAI, chatGPT4
    else:
        raise ValueError("Invalid model specified")

    # Load the prompts from the YAML file based on the language
    lang = language
    yaml_config = f'./resources/prompts/prompts_{lang}.yml'
    with open(yaml_config, 'r', encoding='utf-8') as file:
        prompts = yaml.safe_load(file)
    sysPrompt = prompts[lang]['system_prompts']['translator_prompt_1']
    userPrompt = prompts[lang]['user_prompts']['translator_prompt_1']
    rerunPrompt = prompts[lang]['rerun_prompts']['translation_rerun_prompt']

    if previous_data:
        print(previous_data)

    with open("./input/cl_news.csv", 'r', encoding='utf-8') as csv_file:
        dataframe = pd.read_csv(csv_file)
    language_list = {}

    titles = dataframe['title']
    bodies = dataframe['body']

    print(str(bodies[0]))

    def aiCSVTranslator(content):
        ai_message = []
        for item in content:
        # for body in bodies:
            if model == "chatGPT4" or model == "chatGPT4_bb":
                output = openAI.chat.completions.create(
                    model = chatGPT4,
                    messages = [
                        {"role": "system", "content": f'{sysPrompt}'},
                        {"role": "user", "content": f'{userPrompt}{item}{rerunPrompt}{previous_data}' if previous_data else f'{userPrompt}{item}'}
                    ],
                )
                ai_message = output.choices[0].message.content
                # print(ai_message)

            elif model == "axios" or model == "veritas":
                messages = [
                    SystemMessage(content=f'{sysPrompt}'),
                    HumanMessage(content=f'{userPrompt}{item}')
                ]
                ai_message.append(re.sub(r'<think>[\s\S]*?</think>', '', agent.invoke(messages)))
                # ai_message = agent.invoke(messages)

                # print(ai_message)

            languages = ['English', 'Japanese', 'Korean', 'Simplified Chinese', 'Traditional Chinese', 'Vietnamese']
            language_list = {each_language: [] for each_language in languages}
            for message in ai_message:
                text = message.splitlines()
                text = [space.strip() for space in text if space.strip()]
                # print(text)
                for line in text:
                    leading_word_match = re.match(r'^([^:]+):', line)
                    if leading_word_match:
                        leading_word = leading_word_match.group(1).strip()
                        # print("Leading word: " + leading_word)
                        if leading_word in languages:
                            language_list[leading_word].append(line.split(':', 1)[1].strip())
                            # print("Language list: " + str(language_list))
        return language_list

    titles_dict = aiCSVTranslator(titles)
    bodies_dict = aiCSVTranslator(bodies)

    content_list = [titles_dict, bodies_dict]


    print(content_list)
    for l in content_list[0]:
        print(l + " has the following bodies: " + str(content_list[1][l]))
        # dataframe['title'] = dataframe['title'].replace({title: language_list[language]})
        try:
            dataframe['title'] = content_list[0][l]
            dataframe['body'] = content_list[1][l]
            dataframe.to_csv(f'./output/cl_news_{l}.csv')
        except:
            if error_counter < 3:
                print("Still not getting it right")
                post_translator(language, model, content_list)
                error_counter += 1
            elif error_counter <= 3:
                raise Exception("I give up")
