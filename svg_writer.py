import io, os
from bs4 import BeautifulSoup
import json
import math
import cmath

#Running KiCad Linux vs. standalone requires different imports
try:
    from .parser_base import ParserBase
    from .sexpressions_parser import parse_sexpression
    from .sexpressions_writer import SexpressionWriter
except:
    from parser_base import ParserBase
    from sexpressions_parser import parse_sexpression
    from sexpressions_writer import SexpressionWriter

pxToMM = 3.779528

#Prettifies SVG output, but messes up text field spacing
debug = False
# debug = True

# kicad_pcb
# version
# host
# general
# page
# title_block
# layers
# setup
# net
# net_class
# module
# dimension
# gr_line
# gr_arc
# gr_text
# segment
# via
# zone

class SvgWrite(object):
    def __init__(self):
        print(os.path.dirname(os.path.realpath(__file__)) )
        currentdir = os.path.dirname(os.path.realpath(__file__))
        self.filename_in = os.path.join(currentdir, 'example', 'complex.kicad_pcb')
        # self.filename_in = os.path.join(currentdir, 'example', 'simple.kicad_pcb')
        self.filename_json = os.path.join(currentdir, 'example', 'out.json')
        self.filename_svg = os.path.join(currentdir, 'example', 'out.svg')
        self.filename_base = os.path.join(currentdir, 'example', 'base.svg')
        
        self.hiddenLayers = []


    def Load(self, filename = None):
        if filename is None:
            filename = self.filename_in

        with io.open(filename, 'r', encoding='utf-8') as f:
            sexpression = parse_sexpression(f.read())
        return sexpression

    def Convert(self, obj, save = False):
        js = json.dumps(obj)
        if save:
            with open(self.filename_json, 'wb') as f:
                f.write(js)
        return js

    def Save(self, svg, filename = None):
        if filename is None:
            filename = self.filename_svg

        with open(filename, 'wb') as f:
            f.write(svg)

    def Print_Headings(self, dic):
        for item in dic:
            if type(item) is str:
                print(item)
            else:
                print(item[0])

    def Handle_Headings(self, items, base):
        # svg = ''
        dic = []
        segments = []
        #if items[0] != 'kicad_pcb':
        #    assert False,"kicad_pcb: Not a kicad_pcb"

        base.svg.append(BeautifulSoup('<kicad />', 'html.parser'))

        i = 0
        for item in items:
            if type(item) is str:
                print(item)
            else:
                if item[0] == 'layers':
                    layers = self.Convert_Layers_To_SVG(item)
                   
                    for layer in layers:
                        tag = BeautifulSoup(layer, 'html.parser')
                        base.svg.append(tag)
            i = i + 1
                             
        for item in items:
            if type(item) is str:
                print(item)
            else:
                if item[0] == 'module':
                    base.svg.append(self.Convert_Module_To_SVG(item, i))
            i = i + 1
            
        base.svg.append(BeautifulSoup('<g inkscape:label="Vias" inkscape:groupmode="layer" id="layervia" user="True" />', 'html.parser'))


        for item in items:
            if type(item) is str:
                print(item)
            else:
                # print(item[0])
                if item[0] == 'segment':
                    tag = BeautifulSoup(self.Convert_Segment_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'gr_line':
                    tag = BeautifulSoup(self.Convert_Gr_Line_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)
                    
                elif item[0] == 'gr_poly':
                    tag = BeautifulSoup(self.Convert_Gr_Poly_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'gr_arc':
                    tag = BeautifulSoup(self.Convert_Gr_Arc_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'gr_curve':
                    tag = BeautifulSoup(self.Convert_Gr_Curve_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'gr_text':
                    tag = BeautifulSoup(self.Convert_Gr_Text_To_SVG(item, i), 'html.parser')
                    layer = tag.find('text')['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'zone':
                    tag = BeautifulSoup(self.Convert_Zone_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    if layer:
                        base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'via':
                    tag = BeautifulSoup(self.Convert_Via_To_SVG(item, i), 'html.parser')
                    base.svg.find('g', {'inkscape:label': 'Vias'}, recursive=False).append(tag)
                    
                elif item[0] != 'layers' and item[0] != 'module':
                    # Already handled above
                    svg = self.Convert_Metadata_To_SVG(item)
                    base.svg.kicad.append(BeautifulSoup(svg, 'html.parser'))
                    
            i = i + 1
        dic.append({'segment': segments})

        if debug == True:
            svg = base.prettify("utf-8")
        else:
            svg = base.encode()
        
        return svg



    def Convert_Metadata_To_SVG(self, input):
        # This will just take whatever data and store it in an XML tag as JSON
        # Hacky, but we don't care about it other than to be able to load it back in later

       
        tag = input[0]
        #input = input[1:]
        
        body = json.dumps(input)
        
        svg = '<' + tag + '>'
        svg += body
        svg += '</' + tag + '>'

        return body + ','

    def Convert_Layers_To_SVG(self, input):
        # 0 layers
        # 1
        #   0 1-whatever layerid
        #   1 F.Cu
        #   2/3 user/hide(optional)
        # 2 ...
        # 3 ...

        i = 0
        layers = []
        #print(input)
    
        # if input[0] != 'layers':
        #     assert False,"Layers: Not a layer"
        #     return None

        for item in input:
            i = i + 1
            if i == 1:
                continue

            layerid = item[0]
            layername = item[1]

            user = ''
            hide = ''
            signal = ''
            power = ''
            if 'user' in item:
                user = 'user="True" '
            if 'hide' in item:
                hide = 'hide="True" '
                self.hiddenLayers.append(layername)
            if 'signal' in item:
                signal = 'signal="True" '
            if 'power' in item:
                power = 'power="True" '


            parameters = '<g '
            parameters += 'inkscape:label="' + layername + '" '
            parameters += 'inkscape:groupmode="layer" '
            parameters += 'id="layer' + layerid + '"'
            parameters += 'number="' + layerid + '"'
            parameters += user
            parameters += hide
            parameters += signal
            parameters += power
            parameters += '/>'

            layers.insert(0, parameters)
            i = i + 1
        
        # return {'layers': layers }
        return layers

    def Convert_Segment_To_SVG(self, input, id):
        # 0 segment
        # 1
        #   0 start
        #   1 66.66
        #   2 99.99
        # 2
        #   0 end
        #   1 66.66
        #   2 99.99
        # 3
        #   0 width
        #   1 0.25
        # 4
        #   0 layer
        #   1 B.Cu
        # 5
        #   0 net
        #   1 1

        start = []
        end = []

        if input[0] != 'segment':
            assert False,"Segment: Not a segment"
            return None

        if input[1][0] != 'start':
            assert False,"Segment: Start out of order"
            return None

        start.append(input[1][1])
        start.append(input[1][2])

        if input[2][0] != 'end':
            assert False,"Segment: End out of order"
            return None

        end.append(input[2][1])
        end.append(input[2][2])

        if input[3][0] != 'width':
            assert False,"Segment: Width out of order"
            return None

        width = input[3][1]

        if input[4][0] != 'layer':
            assert False,"Segment: Layer out of order"
            return None

        layer = input[4][1]

        if input[5][0] != 'net':
            assert False,"Segment: Net out of order"
            return None

        net = input[5][1]

        tstamp = ''
        status = ''

        if len(input) > 6:
            if input[6][0] == 'tstamp':
                tstamp = 'tstamp="' + input[6][1] + '" '
            if input[6][0] == 'status':
                status = 'status="' + input[6][1] + '" '
        if len(input) > 7:
            if input[7][0] == 'tstamp':
                tstamp = 'tstamp="' + input[7][1] + '" '
            if input[7][0] == 'status':
                status = 'status="' + input[7][1] + '" '

        parameters = '<path style="fill:none;stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += '" '
        parameters += 'd="M ' + str(float(start[0]) * pxToMM) + ',' + str(float(start[1]) * pxToMM) + ' ' + str(float(end[0]) * pxToMM) + ',' + str(float(end[1]) * pxToMM) + '" '
        # parameters += 'd="M ' + start[0] + ',' + start[1] + ' ' + end[0] + ',' + end[1] + '" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="segment" '
        parameters += 'net="' + net + '" '
        parameters += tstamp
        parameters += status
        parameters += '/>'

        # print(parameters)
        return parameters

    def Convert_Zone_To_SVG(self, input, id):
        # 0 zone
        # 1
        #   0 net
        #   1 16
        # 2
        #   0 net_name
        #   1 GND
        # 3
        #   0 layer
        #   1 B.Cu
        # 4
        #   0 tstamp
        #   1 5EACCA92
        # 5
        #   0 hatch
        #   1 edge
        #   2 0.508
        # 6
        #   0 connect_pads
        #   1
        #     0 clearance
        #     1 0.1524
        # 7
        #   0 min_thickness
        #   1 0.1524
        # 8
        #   0 fill
        #   1 yes
        #   2
        #     0 arc_segments
        #     1 32
        #   3
        #     0 thermal_gap
        #     1 0.1524
        #   4
        #     0 thermal_bridge_width
        #     1 0.1525
        # 9
        #   0 polygon
        #   1
        #     0 pts
        #     1
        #       0 xy
        #       1 147.6375
        #       2 120.9675
        #     2
        #       0 xy
        #       1 147.6375
        #       2 120.9675
        #     3
        #       ...
        # 10
        #   0 filled_polygon
        #   1
        #     0 pts
        #     1
        #       0 xy
        #       1 147.6375
        #       2 120.9675
        #     2
        #       0 xy
        #       1 147.6375
        #       2 120.9675
        #     3
        #       ...
        
        xy_text = ''
        additional = ''
        hide = ''

        for item in input:
                
            if item[0] == 'layer':
                layer = item[1]
                if layer in self.hiddenLayers:
                    hide = ';display:none'
                    
            if item[0] == 'layers':
                #todo
                layer = ''
                
            elif item[0] == 'hatch':
                width = item[2]
                
            elif item[0] == 'polygon':
                for xy in item[1]:
                    if xy[0] == 'xy':
                        xy_text += ' ' + str(float(xy[1]) * pxToMM)
                        xy_text += ',' + str(float(xy[2]) * pxToMM)
                        
            else:
                additional += self.Convert_Metadata_To_SVG(item)

            
        parameters = '<path style="fill:none;stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += hide
        parameters += '" '
        parameters += 'd="M ' + xy_text + ' Z" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="zone">'
        parameters += additional
        parameters += '</path>'

        # print(parameters)
        return parameters

    def Convert_Module_To_SVG(self, input, id):
        # 0 module
        # 1 Diode_SMD:D_SMD_SOD123
        # 2
        #   0 layer
        #   1 B.Cu
        # 3
        #   0 tstamp
        #   1 0DF
        # 4
        #   0 at
        #   1 66.66
        #   2 99.99
        # 3
        #   0 descr
        #   1 0.25
        # 4
        #   0 tags
        #   1 B.Cu
        # 5
        #   0 path
        #   1 1
        # 5
        #   0 attr
        #   1 1
        # 5
        #   0 fp_text / fp_line / fp_text / pad
        #   1 1
        #....
        #....
        # 5
        #   0 model
        #   1 ${KISYS3DMOD}/Package_TO_SOT_SMD.3dshapes/SOT-23-6.wrl
        #   2 offset
        #     0 xyz
        #     1 0
        #     2 0
        #     3 0
        #   3 scale
        #     0 xyz
        #     1 1
        #     2 1
        #     3 1
        #   4 rotate
        #     0 xyz
        #     1 0
        #     2 0
        #     3 0

        at = []
        # svg = BeautifulSoup('<g inkscape:groupmode="layer" type="module" inkscape:label="module' + str(id) + '" id="module' + str(id) + '">', 'html.parser')
        svg = BeautifulSoup('<g type="module" inkscape:label="module' + str(id) + '" id="module' + str(id) + '" name="' + input[1] + '">', 'html.parser')
        
        if input[0] != 'module':
            assert False,"Module: Not a module"
            return None

        a = 0

        for item in input:


            if item[0] == 'at':
                x = float(item[1]) * pxToMM
                y = float(item[2]) * pxToMM
                rotate = 0

                at.append(item[1])
                at.append(item[2])
                transform = 'translate(' + str(x) + ',' + str(y) + ')'

                if len(item) > 3:
                    rotate = float(item[3])
                    transform += ' rotate(' + str(-1 * rotate) + ')'

                svg.g['transform'] = transform

            if item[0] == 'layer':
                svg.g['layer'] = item[1]

            if item[0] == 'tedit':
                svg.g['tedit'] = item[1]

            if item[0] == 'tstamp':
                svg.g['tstamp'] = item[1]

            if item[0] == 'descr':
                svg.g['descr'] = item[1]

            if item[0] == 'tags':
                svg.g['tags'] = item[1]

            if item[0] == 'path':
                svg.g['path'] = item[1]

            if item[0] == 'attr':
                svg.g['attr'] = item[1]

            if item[0] == 'model':
                svg.g['model'] = item[1] + ';'
                #offset
                svg.g['model'] += item[2][1][1] + ',' + item[2][1][2] + ',' + item[2][1][3] + ';'
                #scale
                svg.g['model'] += item[3][1][1] + ',' + item[3][1][2] + ',' + item[3][1][3] + ';'
                #rotate
                svg.g['model'] += item[4][1][1] + ',' + item[4][1][2] + ',' + item[4][1][3] + ';'

            if item[0] == 'fp_line':
                tag = BeautifulSoup(self.Convert_Gr_Line_To_SVG(item, str(id) + '-' + str(a)), 'html.parser')
                svg.g.append(tag)

            if item[0] == 'fp_curve':
                tag = BeautifulSoup(self.Convert_Gr_Curve_To_SVG(item, str(id) + '-' + str(a)), 'html.parser')
                svg.g.append(tag)

            if item[0] == 'fp_text':
                tag = BeautifulSoup(self.Convert_Gr_Text_To_SVG(item, str(id) + '-' + str(a), rotate), 'html.parser')
                svg.g.append(tag)

            elif item[0] == 'pad':
                tag = BeautifulSoup(self.Convert_Pad_To_SVG(item, str(id) + '-' + str(a), rotate), 'html.parser')
                svg.g.append(tag)

            a += 1

        return svg


    def Convert_Gr_Poly_To_SVG(self, input, id):
        # 0 gr_poly
        # 1
        #   0 pts
        #   1
        #     0 xy
        #     1 147.6375
        #     2 120.9675
        #   2
        #     0 xy
        #     1 147.6375
        #     2 120.9675
        #   3
        #     ...
        # 2
        #   0 layer
        #   1 B.Cu
        # 3
        #   0 width
        #   1 0.1
        
        xy_text = ''
        additional = ''
        hide = ''

        for item in input:
                
            if item[0] == 'layer':
                layer = item[1]
                
            elif item[0] == 'width':
                width = item[1]
                
            elif item[0] == 'pts':
                for xy in item:
                    if xy[0] == 'xy':
                        xy_text += ' ' + str(float(xy[1]) * pxToMM)
                        xy_text += ',' + str(float(xy[2]) * pxToMM)
                        
        if layer in self.hiddenLayers:
            hide = ';display:none'
            
        parameters = '<path style="stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';fill:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += hide
        parameters += '" '
        parameters += 'd="M ' + xy_text + ' Z" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="gr_poly" />'
        
        # print(parameters)
        return parameters
        
    def Convert_Gr_Arc_To_SVG(self, input, id):
        # 0 gr_arc
        # 1
        #   0 start
        #   1 66.66
        #   2 99.99
        # 2
        #   0 end
        #   1 66.66
        #   2 99.99
        # 3
        #   0 angle
        #   1 -90
        # 4
        #   0 layer
        #   1 Edge.Cuts
        # 5
        #   0 width
        #   1 0.05
        # 6
        #   0 tstamp
        #   1 5E451B20

        start = []
        end = []
        centre = []
        tstamp = ''

        for item in input:

            # if input[0] != 'gr_arc' and input[0] != 'fp_arc':
            #     assert False,"Gr_arc: Not a gr_arc"
            #     return None

            if item[0] == 'start':

                centre.append(float(item[1]) * pxToMM)
                centre.append(float(item[2]) * pxToMM)

            if item[0] == 'end':

                start.append(float(item[1]) * pxToMM)
                start.append(float(item[2]) * pxToMM)

            if item[0] == 'angle':

                angle = float(item[1])

            if item[0] == 'layer':

                layer = item[1]

            if item[0] == 'width':

                width = item[1]

            if item[0] == 'tstamp':

                tstamp = 'tstamp="' + input[6][1] + '" '

        # m 486.60713,151.00183 a 9.5535717,9.5535717 0 0 1 -9.55357,9.55357
        # (rx ry x-axis-rotation large-arc-flag sweep-flag x y)

        # dx = start[0] - centre[0]
        # dy = centre[1] - start[1]
        # dy = start[1] - centre[1]

        r = (start[0] - centre[0]) + (centre[1] - start[1]) * 1j

        angle = math.radians(angle)
        endangle = cmath.phase(r) - angle
        # print('start angle rad', cmath.phase(r))
        # print('start angle deg', math.degrees(cmath.phase(r)))
        # print('move angle rad', angle)
        # print('move angle deg', math.degrees(angle))
        # print('end angle', math.degrees(endangle))

        end_from_origin = cmath.rect(cmath.polar(r)[0], endangle)
        end = end_from_origin - r
        
        sweep = str(int(((angle / abs(angle)) + 1) / 2))
        if angle > cmath.pi:
            large = '1'
        else:
            large = '0'

        radius = "{:.6f}".format(round(cmath.polar(r)[0], 6))
        end_x = "{:.6f}".format(round(end.real, 6))
        end_y = "{:.6f}".format(round(-end.imag, 6))

        a = ' '.join(['a', radius + ',' + radius, '0', large, sweep, end_x + ',' + end_y])

        parameters = '<path style="fill:none;stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += '" '
        parameters += 'd="M ' + str(start[0]) + ',' + str(start[1]) + ' ' + a + '" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="gr_arc" '
        parameters += tstamp
        parameters += '/>'

        return parameters

    def Convert_Gr_Line_To_SVG(self, input, id):
        # 0 gr_line
        # 1
        #   0 start
        #   1 66.66
        #   2 99.99
        # 2
        #   0 end
        #   1 66.66
        #   2 99.99
        # 3
        #   0 layer
        #   1 Edge.Cuts
        # 4
        #   0 width
        #   1 0.05
        # 5
        #   0 tstamp
        #   1 5E451B20

        start = []
        end = []

        for item in input:
            if type(item) == str:
                #if item == 'gr_line' or item == 'fp_line':
                continue

            if item[0] == 'start':
                start.append(item[1])
                start.append(item[2])

            if item[0] == 'end':
                end.append(item[1])
                end.append(item[2])

            if item[0] == 'layer':
                layer = item[1]

            if item[0] == 'width':
                width = item[1]

            tstamp = ''
            if item[0] == 'tstamp':
                tstamp = 'tstamp="' + item[1] + '" '

        parameters = '<path style="fill:none;stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += '" '
        parameters += 'd="M ' + str(float(start[0]) * pxToMM) + ',' + str(float(start[1]) * pxToMM) + ' ' + str(float(end[0]) * pxToMM) + ',' + str(float(end[1]) * pxToMM) + '" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="gr_line" '
        parameters += tstamp
        parameters += '/>'

        return parameters

    def Convert_Gr_Curve_To_SVG(self, input, id):
        # 0 gr_curve
        # 1
        #   0 pts
        #   1
        #       0 xy
        #       1 99.99
        #       2 99.99
        #   2
        #       0 xy
        #       1 99.99
        #       2 99.99
        #   3
        #       0 xy
        #       1 99.99
        #       2 99.99
        #   4
        #       0 xy
        #       1 99.99
        #       2 99.99
        # 2
        #   0 layer
        #   1 Edge.Cuts
        # 3
        #   0 width
        #   1 0.05
        # 4
        #   0 tstamp
        #   1 5E451B20

        points = []
        
        for item in input:
            if type(item) == str:
                #if item == 'gr_curve' or item == 'fp_curve':
                continue

            #This might have a problem with random list ordering in certain versions of Python
            if item[0] == 'pts':
                for xy in item:
                    if xy[0] == 'xy':
                        points.append(float(xy[1]))
                        points.append(float(xy[2]))

            if item[0] == 'layer':
                layer = item[1]

            if item[0] == 'width':
                width = item[1]

            tstamp = ''
            if item[0] == 'tstamp':
                tstamp = 'tstamp="' + item[1] + '" '


        parameters = '<path style="fill:none;stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += '" '
        parameters += 'd="M ' + str(points[0] * pxToMM) + ',' + str(points[1] * pxToMM) + ' C '
        parameters += str(points[2] * pxToMM) + ',' + str(points[3] * pxToMM) + ' '
        parameters += str(points[4] * pxToMM) + ',' + str(points[5] * pxToMM) + ' '
        parameters += str(points[6] * pxToMM) + ',' + str(points[7] * pxToMM) + '" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="gr_curve" '
        parameters += tstamp
        parameters += '/>'

        return parameters

    def Convert_Gr_Text_To_SVG(self, input, id, r_offset = 0):
        # 0 gr_text
        # 1 text
        # 2
        #   0 at
        #   1 66.66
        #   2 99.99
        # 3
        #   0 layer
        #   1 F.SilkS
        # 4
        #   0 hide
        # 5
        #   0 tstamp
        #   1 F.SilkS
        # 6
        #   0 effects
        #   1 
        #       0 font
        #           1
        #               0 size
        #               1 1.5
        #               2 1.5
        #           2
        #               0 thickness
        #               1 0.3
        #   2
        #       0 justify
        #       1 mirror
        #
        # ---
        # 0 fp_text
        # 1 reference / value / user
        # 2 text
        # 3
        #   0 at
        at = []

        #gr_text is user-created label, fp_text is module ref/value
        if input[0] == 'gr_text':
            type_text = 'gr_text'
            text = input[1]

        if input[0] == 'fp_text':
            type_text = input[1]
            text = input[2]

        effect_text = ''
        transform = ''
        hide = ''
        hidelayer = ''
        tstamp = ''
        mirror_text = ''
        mirror = 1

        for item in input:
            if type(item) == str:
                if item == 'hide':
                    hide = 'hide="True" '

            if item[0] == 'at':
                at.append(item[1])
                at.append(item[2])
                if len(item) > 3:
                    transform += 'rotate(' + str(float(item[3]) + r_offset)+ ')'

            if item[0] == 'layer':
                layer = item[1]
                
            if item[0] == 'tstamp':
                tstamp = 'tstamp="' + item[1] + '" '

            if item[0] == 'effects':
                for effect in item[1:]:
                    if effect[0] == 'font':
                        for param in effect[1:]:
                            if param[0] == 'size':
                                size = [param[1], param[2]]
                            if param[0] == 'thickness':
                                thickness = param[1]
                    elif effect[0] == 'justify':
                        if len(effect) > 1:
                            if effect[1] == 'mirror':
                                transform += ' scale(-1,1)'
                                mirror = -1
                                mirror_text = 'mirrored="true" '
                        
                    else:
                        effect_text = 'effects="' + ';'.join(effect) + '" '
                            


        if len(transform) > 0:
            transform = 'transform="' + transform + '" '
            
        if layer in self.hiddenLayers:
            hidelayer = ';display:none'
            
        parameters = '<text '
        parameters += 'xml:space="preserve" '
        parameters += 'style="font-style:normal;font-weight:normal;font-family:sans-serif'
        parameters += ';fill-opacity:1;stroke:none'
        parameters += hidelayer
        parameters += ';font-size:' + str(float(size[0]) * pxToMM) + 'px'
        parameters += ';fill:#' + self.Assign_Layer_Colour(layer)
        parameters += '" '
        parameters += 'x="' + str(float(at[0]) * pxToMM * mirror) + '" '
        parameters += 'y="' + str(float(at[1]) * pxToMM) + '" '
        parameters += 'id="text' + str(id) + '" '
        parameters += effect_text
        parameters += mirror_text
        parameters += 'layer="' + layer + '" '
        parameters += 'text-anchor="middle" '
        parameters += 'thickness="' + thickness + '" '
        parameters += 'type="' + type_text + '" '
        parameters += tstamp
        parameters += hide
        parameters += transform
        parameters += '>' + text
        parameters += '</text>'

        return parameters

    def Convert_Via_To_SVG(self, input, id):
        # 0 via
        # 1
        #   0 at
        #   1 66.66
        #   2 99.99
        # 2
        #   0 size
        #   1 0.6
        # 3
        #   0 drill
        #   1 0.3
        # 4
        #   0 layers
        #   1 F.Cu
        #   2 B.Cu
        # 5
        #   0 net
        #   1 16

        at = []
        layers = []
        blind = ''
        status = ''
        tstamp = ''

        if input[0] != 'via':
            assert False,"Via: Not a via"
            return None


        for item in input:
            if item[0] == 'at':
                at.append(item[1])
                at.append(item[2])

            if item[0] == 'size':
                size = item[1]

            if item[0] == 'drill':
                drill = item[1]

            if item[0] == 'layers':
                layers.append(item[1])
                layers.append(item[2])

            if item[0] == 'net':
                net = item[1]

            if item == 'blind':
                blind = 'blind=true '

            if item[0] == 'tstamp':
                tstamp = 'tstamp="' + item[1] + '" '
            
            if item[0] == 'status':
                status = 'status="' + item[1] + '" '
         
        parameters = '<g '
        parameters += 'x="' + str(float(at[0]) * pxToMM) + '" '
        parameters += 'y="' + str(float(at[1]) * pxToMM) + '" '
        parameters += 'id="via' + str(id) + '" '
        parameters += 'type="via" '
        parameters += 'layers="' + layers[0] + ',' + layers[1] + '" '
        parameters += 'size="' + size + '" '
        parameters += 'drill="' + drill + '" '
        parameters += 'net="' + net + '" '
        parameters += blind
        parameters += tstamp
        parameters += status
        parameters += '>'

        hole = '<circle style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
        hole += ';fill:#' + self.Assign_Layer_Colour('Via.Inner')
        hole += '" '
        hole += 'cx="' + str(float(at[0]) * pxToMM) + '" '
        hole += 'cy="' + str(float(at[1]) * pxToMM) + '" '
        hole += 'id="viai' + str(id) + '" '
        #hole += 'drill="true" '
        hole += 'r="' + str(float(drill)  * (pxToMM / 2)) + '" '
        hole += '/>'

        parameters += '<circle style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
        parameters += ';fill:#' + self.Assign_Layer_Colour('Via.Outer')
        parameters += '" '
        parameters += 'cx="' + str(float(at[0]) * pxToMM) + '" '
        parameters += 'cy="' + str(float(at[1]) * pxToMM) + '" '
        parameters += 'id="viao' + str(id) + '" '
        parameters += 'r="' + str(float(size)  * (pxToMM / 2)) + '" '
        parameters += 'layers="' + layers[0] + ',' + layers[1] + '" '
        parameters += 'size="' + size + '" '
        parameters += 'drill="' + drill + '" '
        parameters += 'net="' + net + '" '
        parameters += blind
        parameters += tstamp
        parameters += status
        parameters += '/>' + hole 

        parameters += '</g>'

        #print(parameters)
        return parameters

    def Convert_Pad_To_SVG(self, input, id, r_offset = 0):
        # 0 pad
        # 1 1/2/3
        # 2 smd
        # 3 rect
        # 4
        #   0 at
        #   1 66.66
        #   2 99.99
        #   2 180
        # 5
        #   0 size
        #   1 0.9
        #   2 1.2
        # 6
        #   0 layers
        #   1 F.Cu
        #   2 F.Paste
        #   3 F.Mask
        # 7
        #   0 net
        #   1 16
        #   2 Net-(D4-Pad1)

        at = []
        size = []
        layers = []
        roundrect_rratio = ''
        net = ''
        drill = ''
        rotate = ''

        if input[0] != 'pad':
            assert False,"Pad: Not a pad"
            return None

        pin = input[1]

        process = input[2]

        for row in input:
            if len(row) > 1:
                if row[0] == 'at':
                    at.append(float(row[1]))
                    at.append(float(row[2]))

                    if len(row) > 3:
                        start = at[0] + at[1] * 1j
                        angle = math.radians(float(row[3]) - r_offset)
                        endangle = cmath.phase(start) - angle
                        end = cmath.rect(cmath.polar(start)[0], endangle)
                        
                        at[0] = end.real 
                        at[1] = end.imag
                        
                        rotate += 'transform=rotate(' + str(float(row[3]) - r_offset) + ') '
                        rotate += 'rotate = ' + str(float(row[3])) + ' '
                        

                if row[0] == 'size':
                    size.append(row[1])
                    size.append(row[2])

                if row[0] == 'roundrect_rratio':
                    ratio = row[1]
                    roundrect_rratio = 'roundrect_rratio="' + row[1] + '"'

                if row[0] == 'drill':
                    drill = 'drill="' + row[1] + '" '

                if row[0] == 'net':
                    net = 'net="' + row[1] + '" '
                    net += 'netname="' + row[2] + '"'

                if row[0] == 'layers':
                    row = row[1:]

                    for layer in row:
                        layers.append(layer)


        shape = input[3]

        svg = ''
        svgsize = ''
        roundcorners = ''
        first = True

        #Reverse list
        for layer in layers[::-1]:
            parameters = ''
            if shape == 'rect':

                # Corner coordinates to centre coordinate system
                x = at[0] - float(size[0]) / 2
                y = at[1] - float(size[1]) / 2

                parameters += '<rect style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                svgsize += 'x="' + str(x * pxToMM) + '" '
                svgsize += 'y="' + str(y * pxToMM) + '" '
                svgsize += 'width="' + str(float(size[0])  * pxToMM) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            elif shape == 'roundrect':
                
                # Corner coordinates to centre coordinate system
                x = at[0] - float(size[0]) / 2
                y = at[1] - float(size[1]) / 2

                parameters += '<rect style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                roundcorners += 'rx="' + str(float(size[0]) * float(ratio)  * pxToMM) + '" '
                roundcorners += 'ry="' + str(float(size[1]) * float(ratio)  * pxToMM) + '" '
                svgsize += 'x="' + str(x * pxToMM) + '" '
                svgsize += 'y="' + str(y * pxToMM) + '" '
                svgsize += 'width="' + str(float(size[0])  * pxToMM) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            elif shape == 'circle':
                parameters += '<circle style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                svgsize += 'cx="' + str(at[0] * pxToMM) + '" '
                svgsize += 'cy="' + str(at[1] * pxToMM) + '" '
                svgsize += 'r="' + str(float(size[0])  * (pxToMM / 2)) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            elif shape == 'oval':
                parameters += '<circle style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                svgsize += 'cx="' + str(at[0] * pxToMM) + '" '
                svgsize += 'cy="' + str(at[1] * pxToMM) + '" '
                svgsize += 'r="' + str(float(size[0])  * (pxToMM / 2)) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            elif shape == 'custom':
                # todo: Setting custom shape to rect for now
                x = at[0] - float(size[0]) / 2
                y = at[1] - float(size[1]) / 2

                parameters += '<rect style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                svgsize += 'x="' + str(x * pxToMM) + '" '
                svgsize += 'y="' + str(y * pxToMM) + '" '
                svgsize += 'width="' + str(float(size[0])  * pxToMM) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            else:
                assert False,"Pad: Unfamiliar shape: " + shape
                return None

            parameters += ';fill:#' + self.Assign_Layer_Colour(layer)
            parameters += '" '
            parameters += 'id="path-' + str(id) + '-' + layer + '" '
            parameters += svgsize
            parameters += roundcorners
            parameters += roundrect_rratio
            parameters += net
            parameters += rotate
            parameters += drill
            parameters += 'process="' + process + '"'
            parameters += 'pin="' + pin + '"'
            if first == True:
                parameters += 'first="True"'
                parameters += 'layers="' + ','.join(layers) + '"'
            parameters += '/>'

            svg += parameters
            first = False

        #print(parameters)
        return svg

    def Assign_Layer_Colour(self, layername):
        colours = {
            'F.Cu': '840000',
            'In1.Cu': 'C2C200',
            'In2.Cu': 'C200C2',
            'B.Cu': '008400',
            'B.Adhes': '840084',
            'F.Adhes': '000084',
            'B.Paste': '000084',
            'F.Paste': '840000',
            'B.SilkS': '840084',
            'F.SilkS': '008484',
            'B.Mask': '848400',
            'F.Mask': '840084',
            'Dwgs.User': 'c2c2c2',
            'Cmts.User': '000084',
            'Eco1.User': '008400',
            'Eco2.User': 'c2c200',
            'Edge.Cuts': 'C2C200',
            'Margin': 'c200c2',
            'B.CrtYd': '848484',
            'F.CrtYd': 'c2c2c2',
            'B.Fab': '000084',
            'F.Fab': '848484',
            'Via.Outer': 'c2c2c2',
            'Via.Inner': '8c7827',
            'Default': 'FFFF00'
        }

        if layername in colours:
            return colours[layername]
        else:
            return colours['Default']
        
        

    def Run_Standalone(self):
        dic = self.Load()
        
        #Save JSON file, for development
        #self.Convert(dic, True)

        with open(self.filename_base, "r") as f:
    
            contents = f.read()
            base = BeautifulSoup(contents, 'html.parser')
        
        svg = self.Handle_Headings(dic, base)

        self.Save(svg)

   
    def Run_Plugin(self, filename, outfilename):
        dic = self.Load(filename)
        
        with open(self.filename_base, "r") as f:
    
            contents = f.read()
            base = BeautifulSoup(contents, 'html.parser')
        
        outfile = os.path.join(os.path.dirname(filename), outfilename)

        svg = self.Handle_Headings(dic, base)

        self.Save(svg, outfile)



if __name__ == '__main__':
    e = SvgWrite()
    e.Run_Standalone()