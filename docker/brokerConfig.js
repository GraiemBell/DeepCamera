module.exports = {
  protos: ['tcp'],
  host: '127.0.0.1',
  port: 1883,
  wsPort: 3000,
  wssPort: 4000,
  tlsPort: 8883,
  brokerId: 'aedes-cli',
  //credentials: './credentials.json',
  persistence: {
    name: 'redis',
    options: {
      url: 'redis://redis:6379'
    }
  },
  mq: {
    name: 'redis',
    options: {
      url: 'redis://redis:6379'
    }
  },
  key: null,
  cert: null,
  rejectUnauthorized: false,
  verbose: true,
  veryVerbose: true,
  noPretty: false
}
