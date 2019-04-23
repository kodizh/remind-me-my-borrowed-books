#!/usr/bin/env python3
# coding: utf8


from lxml import etree
import logging

"""
The general philosophy is to provide the XML fragment to update, and then get it back.
"""
class Xtemplate:
  def __init__(self):
    self.built_tree = etree

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    pass

  """
  The load_template() method loads a new template file, i.e. the XML file which serves as the base documents
  from which the generated document is created.
  Note that the template document is loaded as a XML file and therefore requires to be a well-formed XML file.
  \filepath the filename to the template document to load.
  """
  def load_template(self, filepath):
    template_content = open( filepath, 'r' )
    xml_fragment = etree.XML( template_content )
    template_content.close()
    return xml_fragment


  """
  The new_value method sets a new value to a given location. The location is a XPath location.
  Just as the set_value method, the new_value method tries to match the whole XPath location
  in the fragment, and in case of failure, the location is reduced iteratively.
  The difference with the set_value method is that in case of match, the new_value method creates
  a new subnode for the first subelement.
  \param xml_fragment the fragment of xml to query against for setting the value
  \param xlocation the XPath expression to set the value at, inside the XML fragment
  \param value the value to set. If None is provided, the element will be created empty
  \return the base element that matched the provided location
  """
  def new_value(self, xml_fragment, xlocation, value=None):
    split = xlocation.split( '/' )
    base_location = '/'.join( split[0:-1] )
    new_element = split[-1]

    base_element, new_elements, location = self.find_matching_element( xml_fragment, base_location )
    new_elements.append(new_element)

    if base_element == None:
      logging.warning( "No matching base location found for entry '{}'. Sought location: '{}'".format(new_element, base_location) )
      base_element = etree.Element( new_elements.pop(0) )

    # and then start creating the new elements
    nb_attr = 0
    while len(new_elements) > nb_attr:
      if new_elements[nb_attr][0] != '@':
        base_element = etree.SubElement( base_element, new_elements.pop(nb_attr) )
      else:
        nb_attr = nb_attr +1

    if value != None:
      if len(new_elements) != 0:
        # case when the last element of the xpath query is an attribute
        base_element.set( new_elements.pop(0)[1:], value )
      else:
        base_element.text = str(value)

    return base_element


  """
  The set_value method sets a value to a given location. The location is a XPath location.
  Just as the new_value method, the set_value method tries to match the whole XPath location
  in the fragment, and in case of failure, the location is reduced iteratively.

  The difference with the new_value method is that in case of match, the set_value method changes
  the value of the first subelement.

  \param xml_fragment the fragment of xml to query against for setting the value
  \param xlocation the XPath expression to set the value at, inside the XML fragment
  \param value the value to set. If None is provided, the element will be created empty
  \return the base element that matched the provided location
  """
  def set_value(self, xml_fragment, xlocation, value=None):
    base_element, new_elements, location = self.find_matching_element( xml_fragment, xlocation )

    if base_element == None:
      print( "No matching location found." )
      base_element = etree.Element( new_elements.pop(0) )

    # and then start creating the new elements
    nb_attr = 0
    while len(new_elements) > nb_attr:
      if new_elements[nb_attr][0] != '@':
        base_element = etree.SubElement( base_element, new_elements.pop(nb_attr) )
      else:
        nb_attr = nb_attr +1

    if value != None:
      if len(new_elements) != 0:
        # case when the last element of the xpath query is an attribute
        base_element.set( new_elements.pop(0)[1:], value )
      else:
        base_element.text = str(value)

    return base_element

  """
  Find the deepest XML element that matches the XPath location. The XPath query is tested
  against the XML fragment. If the two don't match, the XPath query is shortened by one
  element, and the process is repeted until the location matches.
  \param xml_fragment The fragment of XML to search for the provided location
  \param xlocation The location to search in the XML fragment
  \return The value that was returned by the matching location
  \return A list of the elements that didn't match and were removed from the end of the location
  \return The location that eventually match after being shortened
  """
  def find_matching_element( self, xml_fragment, xlocation ):
    if xml_fragment is None:
      location = xlocation.split('/')
      return None, location[1:], '/'

    current_element = xml_fragment.xpath( xlocation )
    short_location = xlocation

    # if not, find out recursively the first existing location
    new_elements = list()
    while len(current_element) == 0:
      split = short_location.split( '/' )
      short_location = '/'.join( split[0:-1] )
      new_elements.insert(0, split[-1])
      current_element = xml_fragment.xpath( short_location )

    return current_element[0], new_elements, short_location

  """
  Returns the root element of the XML document, given any element as returned
  by a XPath query. The method uses the getparent() method until the root is
  found.
  \param element The element that is any subelement of the XML document
  \return The root element of the XML document
  """
  def getroot(self, element):
    parent = element
    while parent.getparent() != None:
      parent = parent.getparent()

    return parent
  """
  Proposed Stub
  Move a specified subtree to another location. The original subtree is removed.
  \param source the location of the top element of the tree to move
  \param dest the location to move the tree to
  """
  def move(self, xml_fragment, xsource, xdest):
    copy(xsource, xdest)
    remove(xsource, xdest)

  """
  Proposed stub
  Copy a specified subtree to another location. The original subtree is kept in place.
  \param source the location of the top element of the tree to move
  \param dest the location to move the tree to
  """
  def copy(self, xml_fragment, xsource, xdest):
    print( "Copying node" )

  """
  Proposed stub
  Removes a specified subtree from the current tree.
  \param location the location of the subtree to remove.
  """
  def remove(self, xml_fragment, xlocation):
    print( "Removing node" )

  """
  Generates the html page from the XML data tree using the given XSL template
  \param xsl_sheet the XSL Sheet that is used to transform the XML tree into HTML
  \return the generated html page
  """
  def transform(self, xml_fragment, xsl_sheet, method=None):
    xslt_root = etree.parse(xsl_sheet)
    transform = etree.XSLT(xslt_root)
    return transform(xml_fragment)

    """ Find the content location """
    """ Get one exerpt and write it out """
    """ Get back to the top of the file and generate the whole """
    """ Try changing one value """
