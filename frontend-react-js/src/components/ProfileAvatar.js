import './ProfileAvatar.css'

export default function ProfileAvatar (props) {
  const backgroundImage = `url("https://assets.cpbc.lightweaver.ca/avatars/${props.id}.jpg")`
  const styles = {
    backgroundImage,
    backgroundSize: 'cover',
    backgroundPosition: 'center'
  }

  return <div className="profile-avatar" style={styles}></div>
}
