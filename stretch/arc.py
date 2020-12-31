    def Parse_Arcs(self, tag, segments):
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

        path = parse_path(tag['d'])
        # print(tag)
        # print(tag['d'])
        # print(path)
        radius = path[0].radius.real / pxToMM
        # angle = '90'
        sweep = path[0].sweep
        large_arc = path[0].large_arc
        # print(segments)


        if bool(large_arc) == True:
            print("Handle~!")

        #KiCad 'start' is actually centre, 'end' is actually svg start
        #SVG end is actual end, we need to calculate centre instead
        # print('path', path[0].start, path[0].end)

        end = [str(path[0].start.real / pxToMM), str(path[0].start.imag / pxToMM)]
        end_complex = (path[0].start.real / pxToMM) + 1j * (path[0].start.imag / pxToMM)
        start_complex = (path[0].end.real / pxToMM) + 1j * (path[0].end.imag / pxToMM)

        q = math.sqrt((end_complex.real - start_complex.real)**2 + (end_complex.real - start_complex.real)**2)

        x3 = (start_complex.real + end_complex.real) / 2
        y3 = (start_complex.imag + end_complex.imag) / 2


        if bool(large_arc) == True:
            #hackhack / fix / whatever:
            #figure out why this is larger than radius sometimes
            print("hackhack: generating janky arc")
            print(radius , q)
            q = q / 2


        if bool(sweep) == False:
            # angle = -angle
            angle = 1
            x = x3 + math.sqrt(radius**2 - (q / 2) ** 2) * (start_complex.imag - end_complex.imag) / q
            y = y3 - math.sqrt(radius**2 - (q / 2) ** 2) * (start_complex.real - end_complex.real) / q
        else:
            # angle = '90'
            angle = -1
            x = x3 - math.sqrt(radius**2 - (q / 2) ** 2) * (start_complex.imag - end_complex.imag) / q
            y = y3 + math.sqrt(radius**2 - (q / 2) ** 2) * (start_complex.real - end_complex.real) / q
   
        start_list = ['start', str(x), str(y)]
        end_list = ['end', end[0], end[1]]

        start_angle = self.Get_Angle([x,y], [path[0].start.real / pxToMM, path[0].start.imag / pxToMM])
        end_angle = self.Get_Angle([x,y], [path[0].end.real / pxToMM, path[0].end.imag / pxToMM])

        angle = angle * (end_angle - start_angle)
        if bool(sweep) == True:
            angle = 360 - angle
        angle = "{:.6f}".format(round(angle, 6))
        
        segments[0] = start_list
        segments[1] = end_list
        segments.insert(2, ([ 'angle', angle]))
        segments.insert(0, 'gr_arc')
        return segments


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