
import streamlit as st
from PIL import Image
from pathlib import Path

from tools.mongo_queries import get_updating_list, ids_to_names



sites = get_updating_list()
names = ids_to_names(sites)
names = [i['name'] for i in names]
items = []


def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()
st.sidebar.markdown("# Main page")

intro_markdown = read_markdown_file("markdown/intro.md")
api_markdown = read_markdown_file("markdown/api.md")
proscons_markdown = read_markdown_file("markdown/proscons.md")
script_markdown = read_markdown_file("markdown/script.md")
traveller_markdown = read_markdown_file("markdown/traveller.md")
st.markdown("# Main page")

for n in names:
    items.append(" - "+n)





st.title("Border Wait Times")

st.markdown("The current ports being polled by the API:\n"+"\n".join(items))


st.markdown(intro_markdown, unsafe_allow_html=True)
image = Image.open('pics/trip.png')

st.image(image, caption='Example trip for Ambassador Bridge')
st.markdown(proscons_markdown,True)
st.markdown(script_markdown,True)
st.markdown(api_markdown,True)
st.markdown(traveller_markdown,True)