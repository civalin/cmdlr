#########################################################################
#  The MIT License (MIT)
#
#  Copyright (c) 2014~2015 CIVA LIN (林雪凡)
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##########################################################################

import hanziconv


class StringProcess():
    trans_component_table = str.maketrans(
        '\?*<":>+[]/', '＼？＊＜”：＞＋〔〕／')
    trans_path_table = str.maketrans(
        '?*<">+[]', '？＊＜”＞＋〔〕')

    def __init__(self, hanzi_mode=None):
        self.__hanzi_mode = hanzi_mode

    def replace_unsafe_characters(self, string):
        return string.translate(type(self).trans_component_table)

    def replace_unsafe_characters_for_path(self, string):
        return string.translate(type(self).trans_path_table)

    def hanziconv(self, string):
        '''convert chinese characters Simplified <-> Trnditional'''
        if self.__hanzi_mode == 'trad':
            string = hanziconv.HanziConv.toTraditional(string)
        elif self.__hanzi_mode == 'simp':
            string = hanziconv.HanziConv.toSimplified(string)
        return string

    def component_modified(self, component):
        safe_component = self.replace_unsafe_characters(component)
        answer = self.hanziconv(safe_component)
        return answer

    def path_modified(self, path):
        safe_path = self.replace_unsafe_characters_for_path(path)
        answer = self.hanziconv(safe_path)
        return answer
