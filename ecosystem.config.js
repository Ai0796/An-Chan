module.exports = {
  apps : [{
    name: 'An Chan',
    script: 'An.py',
    watch: false,
    ignore_watch: '.',
    interpreter: 'python3'
  },
  {
    name: 'Kohane Chan',
    script: 'Kohane.py',
    watch: false,
    ignore_watch: '.',
    interpreter: 'python3'
  },
  {
    name: 'Lemo',
    script: 'Lemo.py',
    watch: false,
    ignore_watch: '.',
    interpreter: 'python3'
  }
  ],

  deploy : {
    production : {
      user : 'SSH_USERNAME',
      host : 'SSH_HOSTMACHINE',
      ref  : 'origin/master',
      repo : 'GIT_REPOSITORY',
      path : 'DESTINATION_PATH',
      'pre-deploy-local': '',
      'post-deploy' : 'npm install && pm2 reload ecosystem.config.js --env production',
      'pre-setup': ''
    }
  }
};
