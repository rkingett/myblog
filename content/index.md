---
layout: layouts/home.njk
numberOfLatestPostsToShow: 15
eleventyNavigation:
  title: Home
  order: 0
---

<a href="/map">The site map has navigation on one page.</a>

Meow. This is my blog and website. I'm scared of being famous but I love people sharing my work.

<a href="/follow">Follow me via feed or emails or anything else, really.</a>

I'm a totally blind, gay, author and accessibility consultant. I used to be legally blind. For more background, check out <a href="/bio/">my about page</a>.

I stutter so <a href="/contact">strongly prefer  written communication.</a>

Below will be some quick links and then the recent posts.

<h1>Key pages.</h1>

* [View everything on one page](/map)
* ]Read all updates](/posts)
* [Learn about my writing](/writings)
* [Financially support me](/support)
* [Learn about my accessibility consulting](/tech)
* [Contact me in a bunch of ways](/contact)
* [View all work I do](/resume)

{% set postsCount = collections.posts | length %}
{% set latestPostsCount = postsCount | min(numberOfLatestPostsToShow) %}

<h1>
Latest {{ latestPostsCount }} Post{% if latestPostsCount != 1 %}s{% endif %}
</h1>

{% set postslist = collections.posts | head(-1 * numberOfLatestPostsToShow) %}
{% set postslistCounter = postsCount %}
{% include "postslist.njk" %}