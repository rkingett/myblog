---
layout: layouts/home.njk
numberOfLatestPostsToShow: 3
eleventyNavigation:
  title: Home
  order: 0
---

{% set postsCount = collections.posts | length %}
{% set latestPostsCount = postsCount | min(numberOfLatestPostsToShow) %}

<h1>
# Latest {{ latestPostsCount }} Post{% if latestPostsCount != 1 %}s{% endif %}
</h1>

{% set postslist = collections.posts | head(-1 * numberOfLatestPostsToShow) %}
{% set postslistCounter = postsCount %}
{% include "postslist.njk" %}
