# Coaction V1
This repository is the first iteration of the Coaction protocol. The Coaction protocol consists of a series of smart contracts and data oracles that create a decentralized validator network powered by the Coaction Network Token (CNT). Validators and delegators alike can earn CNT in a unique "proof-of-delegation" model, burn CNT for boosted staking rewards, or stake CNT for a share of protocol revenue. CNT will eventually be protocol agnostic but initially will be live on only The Graph and the Livepeer network. 

This repository consists of a flask / react web application that hosts a series of smart contracts and python powered data oracles that enable it's core functionalities. It also hosts a leaderboard that is capable of displaying various key economic metrics from a range of network participants. The native CNT token will be deployed on the Arbitrum network. Learn more at https://coaction.network, or contact me directly at max@coaction.network. 

## Installation
Clone the repository to your local machine:

git clone https://github.com/ericmheilman/coaction-v1.git

## Navigate to the project directory:

cd coaction-v1

## Install the required Python packages:

pip install -r requirements.txt


## Start the web server:

python3 ./server/app.py
npm start

Open a web browser and navigate to http://localhost:3000.

The leaderboard will be displayed on the page. The scores are updated every minute

# Contributing
Contributions to the project are welcome. If you find a bug or have a suggestion for a new feature, please create a new issue on GitHub.

# License
This project is licensed under the MIT License. See the LICENSE file for details.

# Credits
This project was created by Max Heilman.


# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
