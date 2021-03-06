#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from tkinter import *
from tkinter import filedialog, messagebox
from obj_generator import *
from prisData import CmpPartData, Part

VERSION = "0.2.1"

class Gui:

    def __init__(self):
        self.filename = ""
        self.output_filename = ""
        self.scale = 1

    def open_input_file(self):
        filename = filedialog.askopenfile(initialdir=f"{os.getcwd()}", title="Select file",
                               filetypes=(("all files", "*.*"), ("3db files", "*.3db"), ("cmp files", "*.cmp") ))
        if filename:
            self.filename = filename
            self.v_input_name.set(self.filename.name)
            self.v_output_name.set(default_output_name(self.filename.name))
            self.v_material_name.set(default_material_name(self.filename.name))

    def open_output_file(self):
        output_filename: str = filedialog.asksaveasfilename(initialdir=f"{os.path.dirname(self.v_output_name.get())}", title="Select file",
                                     filetypes=(("Wavefront OBJ", "*.obj"), ("all files", "*.*")))
        if output_filename:
            self.output_filename = output_filename
            if not self.output_filename.endswith(".obj"):
                self.output_filename += ".obj"

            if self.output_filename:
                self.v_output_name.set(self.output_filename)
                self.v_material_name.set(self.output_filename.replace("obj", "mtl"))

    def load_gui(self):
        self.window = Tk()
        window = self.window
        window.resizable(False, False)
        window.title(f"Extractor {VERSION}")
        title_label = Label(window, text="Conquest: Frontier Wars model extractor", font=("Arial Bold", 16))
        title_label.grid(column=0, row=0)


        #input
        input_frame = LabelFrame(window, text="Input", padx=5, pady=5)

        input_label = Label(input_frame, text="Input file:", padx=10, pady=10)
        input_label.grid(column=0, row=0)

        self.v_input_name = StringVar()
        input_name_entry = Entry(input_frame, textvariable=self.v_input_name, width=80, state="readonly")
        input_name_entry.grid(column=1, row=0)

        input_button = Button(input_frame, text="Browse", command=self.open_input_file)
        input_button.grid(column=2, row=0)

        input_frame.grid(column=0,row=1)


        #output
        output_frame = LabelFrame(window, text="Output", padx=5, pady=5)

        output_label = Label(output_frame, text="Scale:", padx=10, pady=10)
        output_label.grid(column=0, row=0)

        self.v_scale = StringVar()
        self.v_scale.set("1")
        output_name_entry = Entry(output_frame, textvariable=self.v_scale, width=80)
        output_name_entry.grid(column=1, row=0)

        output_label = Label(output_frame, text="Output file:", padx=10, pady=10)
        output_label.grid(column=0, row=1)

        self.v_output_name = StringVar()
        output_name_entry = Entry(output_frame, textvariable=self.v_output_name, width=80, state="readonly")
        output_name_entry.grid(column=1, row=1)

        output_button = Button(output_frame, text="Browse", command=self.open_output_file)
        output_button.grid(column=2, row=1)

        output_frame.grid(column=0, row=2)

        material_label = Label(output_frame, text="Material file:", padx=10, pady=10)
        material_label.grid(column=0, row=2)

        self.v_material_name = StringVar()
        output_name_entry = Entry(output_frame, textvariable=self.v_material_name, width=80, state="readonly")
        output_name_entry.grid(column=1, row=2)

        extract_button = Button(window, text="Extract", command=self.extract)
        extract_button.grid(column=0, row=3)

        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(0, weight=1)

        window.mainloop()

    def extract(self):
        try:
            scale = float(self.v_scale.get())
            extract(self.v_input_name.get(), self.v_output_name.get(), scale)
            messagebox.showinfo("Success", "Object extracted")
        except Exception as ex:
            print(ex)
            messagebox.showerror("Error", ex)

def default_output_name(filename):
    temp = filename.split(".")
    temp[-1] = "obj"
    return ".".join(temp)


def default_material_name(filename):
    temp = filename.split(".")
    temp[-1] = "mtl"
    return ".".join(temp)

def print_help():
    print(f"Extractor Version: {VERSION}")
    print("Usage:")
    print("python extractor.py path/to/file [options]")
    print("Options:")
    print("    -o <file>                           Output file name")
    print("    -s <floating point value>           Scale of the model")
    exit(1)


def get_parent_trans(all_data: List[Part], part: Part):
    parent_part = [x for x in all_data if x.child_name == part.parent_name]
    if parent_part:
        this_part = parent_part[0]
        this_trasnform = this_part.trans_mat()
        parent_tansform = get_parent_trans(all_data, this_part)
        return np.matmul(this_trasnform, parent_tansform)
    else:
        return np.identity(4)

def extract(filename, output_filename, scale):
    a = UtfFile()
    model_data = a.load_utf_file(filename)
    if filename.endswith('.3db'):
        g = ObjModel()
        g.export_to_obj(model_data['\\']['openFLAME 3D N-mesh'], output_filename, scale)
    elif filename.endswith('.cmp'):
        already_calculated_values = {}
        basename = output_filename
        v = model_data['\\']['Cmpnd']
        all_data: List[Part] = []
        if 'Pris' in v['Cons']:
            prisData = CmpPartData(v['Cons']['Pris'])
            all_data.extend(prisData.parts)
        # print(prisData.parts)
        if 'Rev' in v['Cons']:
            revData = CmpPartData(v['Cons']['Rev'])
            all_data.extend(revData.parts)
        # print(revData.parts)
        for k, v in model_data['\\'].items():
            if k.endswith('.3db'):
                a = basename.split(".")
                a[-2] += "_" + k.split(".")[0]
                output_filename = ".".join(a)
                g = ObjModel()
                pos_data: List[Part] = [x for x in all_data if k.startswith(x.child_name)]
                local_transform = np.identity(4)
                if pos_data:
                    pos_data_t: Part = pos_data[0]
                    parent_transform = get_parent_trans(all_data, pos_data_t)
                    child_transform = pos_data_t.trans_mat()
                    local_transform = np.matmul(child_transform, parent_transform)
                g.export_to_obj(v['openFLAME 3D N-mesh'], output_filename, scale, local_transform)
    print("Done")


if __name__ == '__main__':

    scale = 1
    output_filename = ""

    if len(sys.argv) > 6:
        print("Invalid number of arguments!")
        print_help()
    elif len(sys.argv) == 1:
        gui = Gui()
        gui.load_gui()
    elif len(sys.argv) == 2:
        output_filename = default_output_name(sys.argv[1])
    elif len(sys.argv) == 4:
        options = {sys.argv[2][1:]: sys.argv[3]}
        if "o" in options.keys():
            output_filename = options["o"]
        elif "s" in options.keys():
            try:
                scale = float(options["s"])
            except:
                print(f"Invalid scale value: {options['s']}")
                print_help()
            output_filename = default_output_name(sys.argv[1])
        else:
            print("Invalid parameter!")
            print_help()
    elif len(sys.argv) == 6:
        options = {sys.argv[2][1:]: sys.argv[3], sys.argv[4][1:]: sys.argv[5]}
        if "o" in options.keys():
            output_filename = options["o"]
        else:
            print("Invalid parameter!")
            print_help()
        if "s" in options.keys():
            try:
                scale = float(options["s"])
            except:
                print(f"Invalid scale value: {options['s']}")
                print_help()
        else:
            print("Invalid parameter!")
            print_help()

    if len(sys.argv) != 1:
        filename = sys.argv[1]
        extract(filename, output_filename, scale)



