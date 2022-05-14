## 1.3.1 (2022-05-14)

* Bugfix (all): fix error handling for APIs that don't give a dict in the response ([Alex Wuillaume](https://github.com/wuillaumea))

## 1.3.0 (2022-03-13)

* Addition (local): Added `local` backend for running directly on Proxmox hosts. ([Markus Reiter](https://github.com/reitermarkus))
* Bugfix (all): properly parse command string sent to QEMU guest agent ([John Hollowell](https://github.com/jhollowe))
* Improvement (command_base): Refactor code to have a unified CLI backend base for `openssh`, `ssh_paramiko`, and `local` backends ([Markus Reiter](https://github.com/reitermarkus))
* Improvement (https): Support IPv6 addresses (TODO)[https://github.com/TODO]
* Improvement: Move CI to GitHub actions from Travis.ci ([John Hollowell](https://github.com/jhollowe))
* Improvement: Cleanup documentaiton and move to dedicated site ([John Hollowell](https://github.com/jhollowe))
* Improvement: Add `pre-commit` hooks for formatting and linting and format all code ([John Hollowell](https://github.com/jhollowe))

## 1.2.0 (2021-10-07)
* Addition (https): Added OTP code support to authentication ([John Hollowell](https://github.com/jhollowe))
* Addition (https): Added support for large file uploads using requests_toolbelt module ([John Hollowell](https://github.com/jhollowe))
* Addition (all): Added support for Proxmox Mail Gateway (PMG) and Proxmox Backup Server (PBS) with parameter validation ([Gabriel Cardoso de Faria](https://github.com/gabrielcardoso21), [John Hollowell](https://github.com/jhollowe))
* Addition (all): Added detailed information to ResourceException ([mihailstoynov](https://github.com/mihailstoynov))
* Bugfix (base_ssh): Resolved issue with values containing spaces by encapsulating values in quotes ([mihailstoynov](https://github.com/mihailstoynov))
* Bugfix (all): Resolved issue with using get/post/push/delete on a base ProxmoxAPI object ([John Hollowell](https://github.com/jhollowe))
* Bugfix (all): Added support for responses which are not JSON ([John Hollowell](https://github.com/jhollowe))
* Improvement: Added and updated documentation ([Ananias Filho](https://github.com/ananiasfilho), [Thomas Baag](https://github.com/b2ag))
* Improvement: Tests are now not installed when using PIP ([Ville Skyttä](https://github.com/scop))
* Addition: Devcontainer definition now available to make development easier ([John Hollowell](https://github.com/jhollowe))

## 1.1.1 (2020-06-23)
* Bugfix (https): correctly renew ticket in the session, not just the auth ([John Hollowell](https://github.com/jhollowe))

## 1.1.0 (2020-05-22)
* Addition (https): Added API Token authentication ([John Hollowell](https://github.com/jhollowe))
* Improvement (https): user/password authentication refreshes ticket to prevent expiration ([CompileNix](https://github.com/compilenix), [John Hollowell](https://github.com/jhollowe))
* Bugfix (ssh_paramiko): Handle empty stderr from ssh connections ([morph027](https://github.com/morph027))
* DEPRECATED (https): using ``auth_token`` and ``csrf_token`` (ProxmoxHTTPTicketAuth) is now deprecated. Either pass the ``auth_token`` as the ``password`` or use the API Tokens.

## 1.0.4 (2020-01-24)
* Improvement (https): Added timeout to authentication (James Lin)
* Improvement (https): Handle AnyEvent::HTTP status codes gracefully (Georges Martin)
* Improvement (https): Advanced error message with error code >=400 ([ssi444](https://github.com/ssi444))
* Bugfix (ssh): Fix pvesh output format for version > 5.3 ([timansky](https://github.com/timansky))
* Transferred development to proxmoxer organization

## 1.0.3 (2018-09-10)
* Improvement (https): Added option to specify port in hostname parameter ([pvanagtmaal](https://github.com/pvanagtmaal))
* Improvement: Added stderr to the Response content ([Jérôme Schneider](https://github.com/merinos))
* Bugfix (ssh_paramiko): Paramiko python3: stdout and stderr must be a str not bytes ([Jérôme Schneider](https://github.com/merinos))
* New lxc example in docu ([Geert Stappers](https://github.com/stappersg))

## 1.0.2 (2017-12-02)
* Tarball repackaged with tests

## 1.0.1 (2017-12-02)
* LICENSE file now included in tarball
* Added verify_ssl parameter to ProxmoxHTTPAuth ([Walter Doekes](https://github.com/wdoekes))

## 1.0.0 (2017-11-12)
* Update Proxmoxer readme ([Emmanuel Kasper](https://github.com/EmmanuelKasper))
* Display the reason of API calls errors ([Emmanuel Kasper](https://github.com/EmmanuelKasper), [kantsdog](https://github.com/kantsdog))
* Filter for ssh response code ([Chris Plock](https://github.com/chrisplo))

## 0.2.5 (2017-02-12)
* Adding sudo to execute CLI with paramiko ssh backend ([Jason Meridth](https://github.com/jmeridth))
* Proxmoxer/backends/ssh_paramiko: improve file upload ([Jérôme Schneider](https://github.com/merinos))

## 0.2.4 (2016-05-02)
* Removed newline in tmp_filename string ([Jérôme Schneider](https://github.com/merinos))
* Fix to avoid module reloading ([jklang](https://github.com/jklang))

## 0.2.3 (2016-01-20)
* Minor typo fix ([Srinivas Sakhamuri](https://github.com/srsakhamuri))

## 0.2.2 (2016-01-19)
* Adding sudo to execute pvesh CLI in openssh backend ([Wei Tie](https://github.com/TieWei), [Srinivas Sakhamuri](https://github.com/srsakhamuri))
* Add support to specify an identity file for ssh connections ([Srinivas Sakhamuri](https://github.com/srsakhamuri))

## 0.2.1 (2015-05-02)
* fix for python 3.4 ([kokuev](https://github.com/kokuev))

## 0.2.0 (2015-03-21)
* Https will now raise AuthenticationError when appropriate. ([scap1784](https://github.com/scap1784))
* Preliminary python 3 compatibility. ([wdoekes](https://github.com/wdoekes))
* Additional example. ([wdoekes](https://github.com/wdoekes))

## 0.1.7 (2014-11-16)
* Added ignore of "InsecureRequestWarning: Unverified HTTPS request is being made..." warning while using https (requests) backend.

## 0.1.4 (2013-06-01)
* Added logging
* Added openssh backend
* Tests are reorganized

## 0.1.3 (2013-05-30)
* Added next tests
* Bugfixes

## 0.1.2 (2013-05-27)

* Added first tests
* Added support for travis and coveralls
* Bugfixes

## 0.1.1 (2013-05-13)
* Initial try.
