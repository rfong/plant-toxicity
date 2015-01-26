from bs4 import BeautifulSoup
from enum import Enum
import os
import requests
import json
import urlparse


class FieldType(Enum):
  string = 1
  link = 2
  image = 3

def extract_content(field_type, tag, selector=None):
  """Extract content from a tag."""
  tag = get_child_tag(tag, selector)
  if not tag:
    return None
  if field_type == FieldType.string:
    return tag.string
  if field_type == FieldType.link:
    return tag['href']
  if field_type == FieldType.image:
    return tag['src']

def get_child_tag(tag, selector=None):
  """Use selector to acquire first matching child of tag."""
  if selector:
    tag = tag.select(selector)
    if len(tag) == 0:
      return None
    return tag[0]
  return tag

def get_domain(url):
  """Given a url, get its domain."""
  parsed_uri = urlparse.urlparse(url)
  domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
  return domain

def select(url, selector):
  """Given url and selector, select elements from page."""
  return BeautifulSoup(requests.get(url).content).select(selector)

def get_data(tags, field_params):
  """
  :param tags: List of HTML tags as extracted by BeautifulSoup.
  :param field_params: List of dictionaries each specifying parameters for
    a column of data to be extracted. Each column has:
    name <string>
    type <FieldType>
    (optional) selector <string> specifying css selector to use on given tag
  :returns: A list of dictionaries representing the field evaluations.
  """
  # For each tag, evaluate all the field values.
  # We are lazy and always use the transformer in the nested comprehension,
  # so let's set dummy reflexive lambdas to be the default.
  return [
    { field['name']: field.get('transformer', lambda x:x)(
        extract_content(field['type'], tag,
                        selector=field.get('selector', None)))
      for field in field_params }
    for tag in tags
  ]

def postprocess(infile_name, outfile_name):
  """Once main() has been run, apply additional transformations."""
  data = json.loads(open(infile_name, 'r').readline())
  
  def tox_by_animal(string):
    """Given the ASPCA toxicity description, check which animals apply."""
    string = string.lower()
    return { animal: animal in string
             for animal in ['cats', 'dogs', 'horses'] }

  def all_toxicity_stati(toxicity, non_toxicity):
    """
    Return toxicity and non-toxicity status for each animal from the ASPCA
    toxicity description strings.
    """
    ret = {
      'toxicity-'+animal: status
      for animal, status in tox_by_animal(toxicity).iteritems() }
    ret.update({
      'non-toxicity-'+animal: status
      for animal, status in tox_by_animal(non_toxicity).iteritems() })
    return ret

  # Update with additional toxicity info
  for row in data:
    row.update(all_toxicity_stati(
      row['toxicity'] or '',
      row['non-toxicity'] or ''
    ))

  # All hyphens in keys must go to underscores.
  for row in data:
    for key, val in row.iteritems():
      if '-' in key:
        row[key.replace('-', '_')] = val
        del row[key]

  # Write back out
  with open(outfile_name, 'w') as outfile:
    json.dump({'data': data}, outfile)

def main():
  PAGES = 67
  url = 'https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants'
  domain = get_domain(url)
  paginated_url_template = url + "?page={page}"

  # Paginated urls [0-PAGES)
  urls = [paginated_url_template.format(page=page) for page in xrange(PAGES)]

  # Scrape overview page to get links to all individual pages.
  plant_data = []
  for i, url in enumerate(urls):
    plant_tags = select(
      url, '.view-plant-list-view .views-field-title .field-content')
    fields = [
      { 'name': 'name',
        'type': FieldType.string,
        'selector': '.plant-title-name',
      },
      { 'name': 'url',
        'type': FieldType.link,
        'selector': 'a',
        'transformer': lambda link: domain + link,
      },
    ]
  
    plant_data += get_data(plant_tags, fields)
    print "Scraped overview page", i
  print "Finished obtaining all links from overview pages"

  # Checkpoint
  with open('links.json', 'w') as outfile:
    json.dump({'data': plant_data}, outfile)

  print "Preparing to scrape individual pages..."

  # Field specifications for individual pages.
  detail_field_names = [
    'additional-common-names', 'scientific-name', 'family', 'non-toxicity',
    'toxicity', 'toxic-principles', 'clinical-signs',
  ]
  detail_fields = [
    { 'name': name,
      'type': FieldType.string,
      'selector': '.field-name-field-%s span.values' % name,
    } for name in detail_field_names
  ]
  detail_fields.append({
    'name': 'image-url',
    'type': FieldType.image,
    'selector': '.field-name-field-image img',
  })
  # Scrape individual pages.
  for i, plant in enumerate(plant_data):
    tag = select(plant['url'], '.page-content .panel-panel')
    # Should only find one matching tag, and therefore one row of data.
    data = get_data(tag, detail_fields)[0]
    plant.update(data)
    if i%10 == 0:
      print "Scraped individual page", i

  # Dump everything because who cares about memory
  print "Dumping all data to JSON..."
  with open('raw_data.json', 'w') as outfile:
    json.dump({'data': plant_data}, outfile)

  print "Done."


if __name__ == '__main__':
  main()
