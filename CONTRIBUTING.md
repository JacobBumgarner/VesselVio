# Contributing to VesselVio

Contributions to VesselVio are absolutely welcome, and I thank you for being interested in expanding this project!

Reading and following these guidelines will help us make the contribution process easy and effective for everyone involved. It also communicates that you agree to respect my time as a developer as I manage and develop VesselVio. In return, I will reciprocate that respect by addressing your issue, assessing changes, and helping you finalize your pull requests.

## Outline

* [Code of Conduct](#code-of-conduct)
* [Getting Started](#getting-started)
    * [Issues](#issues)
    * [Pull Requests](#pull-requests)
* [Contribution Guide](#contribution-guide)
    * [Outline](#outline)
    * [Style Checking](#style-checking)
    * [Unit Testing](#unit-testing)
* [Getting Help](#getting-help)

## Code of Conduct

I take the community surrounding VesselVio seriously and hold myself and others to high standards of communication. By participating and conributing in this project, you agree to uphold our [Code of Conduct](https://github.com/JacobBumgarner/VesselVio/blob/main/CODE_OF_CONDUCT.md).


## Getting Started

Contributions are made to this repo via Issues and Pull Requests (PRs). A few general guidelines that cover both:

- Search for existing Issues and PRs before creating your own.
- I work hard to address issues and handle them in a timely manner. But depending on the impact, it could take a while to investigate the root cause. A friendly ping in the comment thread to the submitter or me can help draw attention if your issue is blocking.
- If you've never contributed before, see [this guide to contributing to open-source projects](https://opensource.guide/how-to-contribute/) for resources and tips on how to get started.

### Issues

Issues should be used to report bugs in the application, highligth issues with the library, or request a new feature. When you create a new Issue, a template will be loaded that will guide you through collecting and providing the information we need to investigate. If you are looking to find guidance on using the application, please instead open a [discussion](https://github.com/JacobBumgarner/VesselVio/discussions) thread or [reach out to me](https://communityinviter.com/apps/vesselvio/join-vesselvio-on-slack) on Slack!

If you find an Issue that addresses the problem you're having, please add your own reproduction information to the existing issue rather than creating a new one. Adding a [reaction](https://github.blog/2016-03-10-add-reactions-to-pull-requests-issues-and-comments/) can also help be indicating that a particular problem is affecting more than just the reporter.

### Pull Requests

PRs to VesselVio are always welcome and can be a quick way to get your fix or improvement slated for the next release. In general, PRs should:

- Only fix/add the functionality in question **OR** address wide-spread whitespace/style issues, not both.
- Add unit or integration tests for fixed or changed functionality (if a test suite already exists).
- Address a single concern in the least number of changed lines as possible.
- Include documentation in the repo
- Be accompanied by a complete Pull Request template (loaded automatically when a PR is created).

For changes that address core functionality or would require breaking changes (e.g. a major release), it's best to open an Issue to discuss your proposal first. This is not required but can save time creating and reviewing changes.

In general, I work to follow [Trunk Based Development](https://github.com/susam/gitpr](https://trunkbaseddevelopment.com/), much like that of [PyVista](https://github.com/pyvista/pyvista). 

## Contribution Guide

### Outline
If you plan to contribute a new feature to VesselVio, below is the general set of steps you will follow.
1. Fork the repository to your own Github account
2. Clone the project to your machine
3. Create a branch locally with a succinct but descriptive name
4. Commit changes to the branch, including unit tests
5. Run the `pre-commit` for style checking (see below)
6. Run the unit tests to ensure code coverage stays consistent (see below)
7. Push changes to your fork
8. Open a PR in our repository and follow the PR template so that I can efficiently review the changes.

### Style Checking
I adhere to PEP8 as much as possible, except for line widths in GUI code, which instead of 79 characters can be a maximum of 99 characters for code. Ideally, you should strive to meet the 79 character criteria, but PyQt can be a bit of a pain in this regard.

To check the style of your code (as in step 5 in the outline), you should use `pre-commit`. First, you should install `pre-commit` as below and install it as a pre-commit hook as below.
```
pip install pre-commit
pre-commit install
```

Now, the stylechecks specific to VesselVio will be run prior to any commits. You can also test your code prior to commits using:
```
pre-commit run --all-files
```

Following this will ensure that your commits adhere to the general style guidelines of VesselVio.

Lastly, variable and object naming conventions in VesselVio differ between the model and view code. All model/backend pipeline variable naming should adhere to PEP8 conventions. GUI variable naming should adhere to the style provided by PyQt. For example, if you're creating a button, the button variable should be `myButton`, not `my_button`. This helps me to distinguish between model and view code! 

### Unit Testing
You should always ensure that the code you're adding is being tested. This will prolong the life and stability of the VesselVio codebase. If a relevant `test_*.py` file exists for your PR, add test functions to cover your code. If not, then you should create a new file and add the relevant tests.

Unit testing can be conducted by installing required packages as below:
```
pip install requirements_test.py
```

Then, you should test your code and examine coverage as below to determine that coverage hasn't reduced. Use the generated HTML file to view where your code is and isn't covered by the unit testing. Aim for > 90% coverage!

```
coverage run -m pytest .
coverage html
```

## Getting Help

Join us in the [VesselVio Slack Community](https://communityinviter.com/apps/vesselvio/join-vesselvio-on-slack) and post your question there or shoot me a direct message!
