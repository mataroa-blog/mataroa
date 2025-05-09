# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0](https://github.com/mataroa-blog/mataroa/compare/v1.1...v1.2) - 2025-02-06

### Important changes

* Change project license from MIT to AGPL-3.0-only
* Enable customisation of subscribe note on footer
* Introduce ansible configuration for deployment
* Switch jobs from cron to systemd timers
* Replace uWSGI with Gunicorn
* Replace black/flake8/isort with ruff
* Refactor newsletter processing into more robust and simpler workflow
* Setup docs using mdbook
* Improve docker local development setup
* Add guide for custom domains
* Simplify Zola and Hugo base CSS styles
* Add themed error pages
* Upgrade to Django 5.1
* Limit RSS to last 10 posts

### Bugfixes

* Fix Zola v0.19 RSS feed configuration

## [1.1.0](https://github.com/mataroa-blog/mataroa/compare/v1.0...v1.1) - 2023-12-05

### Important changes

* Rewrite moderation dashboard
* Rewrite Stripe integration with latest APIs
* Create new signup workflow
* Lower image size limit to 1MB
* Upgrade to Django 5.0

## [1.0.0](https://github.com/mataroa-blog/mataroa/compare/5ff277da71fb653631ea38407cd6154e831be540...v1.0) - 2023-09-06

This is an initial numbered release after 3+ years of development.

* Core blogging functionalities
* Export functionalities
* Email newsletter
* Custom domains
* Backend-based analytics
* API
