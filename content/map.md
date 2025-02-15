---
title: Site Map
eleventyNavigation:
  key: Site Map
  order: 2
---

TODO

Pages, not posts, and tags

{%- for page in collections.all %}
{% set absoluteUrl %}{{ page.url | htmlBaseUrl(metadata.url) }}{% endset %}

- [{{ page.data.title }}]({{ absoluteUrl }})
  {%- endfor %}
