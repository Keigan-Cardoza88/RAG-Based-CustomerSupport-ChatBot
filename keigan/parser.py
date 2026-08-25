# This file contains the code for basically getting all relevant 
# info from the knowledge base into a clean llm ready format.
import pprint
from pathlib import Path

def parser(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as rpc: # we get some charmap error if utf-8 not specified
        text = rpc.read()
        parts = text.split("---", 2)
        front_matter = parts[1].strip()
        content = parts[2].strip()

        # print(front_matter, content)
        front_matter_dict = {}
        for line in front_matter.splitlines():
            key, value = line.split(":", 1)
            front_matter_dict[key.strip()] = value.strip()
    
        sections = content.split("## ")
        title = sections[0].split("# ")[1].strip()

        chunks = []
        for section in sections[1:]:
            lines = section.splitlines()
            section_title = lines[0].strip()
            section_content = "\n".join(lines[1:]).strip()
            chunk_metadata = front_matter_dict.copy()
            chunk_metadata["section"] = section_title
            chunk_metadata["filename"] = Path(file_path).name
            chunk = {
                "content": f"{title}\n\n{section_title}\n\n{section_content}",
                "metadata": chunk_metadata
            }
            chunks.append(chunk)

        current_file_knowledge = {
            "chunks": chunks
        }
        return current_file_knowledge