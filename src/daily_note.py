import yaml, re
from datetime import timedelta, datetime
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

class TimelogEntry(object):
    def __init__(self) -> None:
        self.start_dt = None
        self.delta_time = None

class DailyNote(object):
    def __init__(self) -> None:
        self.front_matter_obj = None
        self.timelog = list()

    def read_front_matter(self, root_node):
        front_matter_node = root_node.children[0]
        if front_matter_node.info == "yaml":
            self.front_matter_obj = yaml.safe_load(front_matter_node.content)

    def read_all_section(self, root_node):
        sub_section_nodes = root_node[1]
        assert(sub_section_nodes.type == "bullet_list")
        for section in sub_section_nodes.children:
            section_title = section.children[0].children[0].content
            if section_title == "Timelog":
                self.read_timelog(section.children[1])
            print(section_title)
        
    def read_timelog(self, timelog_node):
        for timelog_entry_node in timelog_node.children:
            if len(timelog_entry_node.children) <= 0:
                # Dummy entry 
                continue
            content = timelog_entry_node.children[0].children[0].content
            self.add_timelog(content)

    def add_timelog(self, content):
        time_span_str, sub_content = content.split(" ", maxsplit=1)
        tags = re.findall(r"#\S+", sub_content)
        
        print(time_span_str, "|", sub_content, )

    def set_content(self, content):
        md_obj = MarkdownIt("commonmark")
        tokens = md_obj.parse(content)
        node = SyntaxTreeNode(tokens)
        self.read_front_matter(node)
        self.read_all_section(node)
        
        # print(node.children[0].info)
        # print(node.children[1], node.children[1].children[0].children[1].children[1].children[0].children[0].content)
        # yaml_obj = yaml.safe_load(node.children[0].content)
        # print(yaml_obj)