import { Auth } from 'aws-amplify'

export async function checkAuth (setUser) {
  Auth.currentAuthenticatedUser({
    // Optional, By default is false.
    // If set to true, this call will send a
    // request to Cognito to get the latest user data
    bypassCache: false
  })
    .then((cognito_user) => {
      setUser({
        cognito_user_uuid: cognito_user.attributes.sub,
        display_name: cognito_user.attributes.name,
        handle: cognito_user.attributes.preferred_username
      })
    })
    .catch((err) => console.log(err))

  // This needs fetch and set the bearer token because it's only valid for 1 hour
  // https://docs.amplify.aws/lib/auth/manageusers/q/platform/js/#retrieve-current-authenticated-user
  Auth.currentSession().then((cognito_session) => {
    if (
      localStorage.getItem('access_token') !==
      cognito_session.getAccessToken().jwtToken
    ) {
      console.log('refreshing JWT', cognito_session.getAccessToken().jwtToken)
      localStorage.setItem(
        'access_token',
        cognito_session.getAccessToken().jwtToken
      )
    }
  })
}

export async function getAccessToken () {
  Auth.currentSession()
    .then((cognito_user_session) => {
      const access_token = cognito_user_session.accessToken.jwtToken
      localStorage.setItem('access_token', access_token)
    })
    .catch((err) => console.log(err))
}
