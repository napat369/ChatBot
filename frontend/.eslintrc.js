module.exports = {
    "env": {
        "browser": true,
        "es2021": true,
        "node": true
    },
    "extends": [
        "plugin:vue/vue3-essential",
        "eslint:recommended"
    ],
    "parserOptions": {
        "ecmaVersion": 12,
        "parser": "@babel/eslint-parser",
        "sourceType": "module",
        "requireConfigFile": false,
        "babelOptions": {
            "presets": ["@babel/preset-env"]
        }
    },
    "plugins": [
        "vue"
    ],
    "rules": {
        'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
        'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off'
    }
};
