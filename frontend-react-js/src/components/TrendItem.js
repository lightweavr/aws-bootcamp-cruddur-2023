import './TrendItem.css'

export default function TrendItem (props) {
  const commify = (n) => {
    const parts = n.toString().split('.')
    const numberPart = parts[0]
    const decimalPart = parts[1]
    const thousands = /\B(?=(\d{3})+(?!\d))/g
    return (
      numberPart.replace(thousands, ',') +
      (decimalPart ? '.' + decimalPart : '')
    )
  }

  return (
    // eslint-disable-next-line jsx-a11y/anchor-is-valid
    <a className="trending" href="#">
      <span className="hashtag">#{props.hashtag}</span>
      <span className="count">#{commify(props.count)} cruds</span>
    </a>
  )
}
