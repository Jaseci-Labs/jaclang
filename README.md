# Jaseci 2

The next generation is upon us... (In ideation and specification phase)

## Set up Node in Ubuntu 
### Prerequisite: To follow this guide, you will need an Ubuntu 20.04 server set up. Before you begin, you should have a non-root user account with `sudo` privileges set up on your system . If not, you can follow this [link](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-20-04) to set this up.

### Option 1 — Installing Node.js with Apt from the Default Repositories
Ubuntu 20.04 contains a version of Node.js in its default repositories that can be used to provide a consistent experience across multiple systems. At the time of writing, the version in the repositories is 10.19. This will not be the latest version, but it should be stable and sufficient for quick experimentation with the language.

```
Warning: the version of Node.js included with Ubuntu 20.04, version 10.19, is now unsupported and unmaintained.
You should not use this version in production, and should refer to one of the other
sections in this tutorial to install a more recent version of Node.
```
To get this version, you can use the `apt` package manager. Refresh your local package index first:
```bash
 sudo apt update
```
Then install Node.js:
```bash
 sudo apt install nodejs
```
Check that the install was successful by querying node for its version number:
```bash
 node -v
```
If the package in the repositories suits your needs, this is all you need to do to get set up with Node.js. In most cases, you’ll also want to also install npm, the Node.js package manager. You can do this by installing the npm package with apt:

```
 sudo apt install npm
```

This allows you to install modules and packages to use with Node.js.

### Option 2 — Installing Node.js with Apt Using a NodeSource PPA
To install a different version of Node.js, you can use a PPA (personal package archive) maintained by NodeSource. These PPAs have more versions of Node.js available than the official Ubuntu repositories. Node.js v16 and v18 are available as of the time of writing.

First, install the PPA to get access to its packages. From your home directory, use curl to retrieve the installation script for your preferred version, making sure to replace 16.x with your preferred version string (if different):

```
 cd ~
 curl -sL https://deb.nodesource.com/setup_16.x -o /tmp/nodesource_setup.sh
```
Refer to the [NodeSource documentation](https://github.com/nodesource/distributions/blob/master/README.md) for more information on the available versions.

Inspect the contents of the downloaded script with nano or your preferred text editor:

```
 nano /tmp/nodesource_setup.sh
```
When you are satisfied that the script is safe to run, exit your editor. Then run the script with sudo:
```
 sudo bash /tmp/nodesource_setup.sh
```
The PPA will be added to your configuration and your local package cache will be updated automatically. You can now install the Node.js package in the same way you did in the previous section:
```
 sudo apt install nodejs
```
Verify that you’ve installed the new version by running node with the -v version flag:
```
node -v
```

The NodeSource nodejs package contains both the `node` binary and `npm`, so you don’t need to install `npm` separately.



Get to the docs, check the guidelines on how to contribute. 

## Getting Docs Up Locally

Go to `/docs` base dir and run

```bash
yarn install
yarn start
```
