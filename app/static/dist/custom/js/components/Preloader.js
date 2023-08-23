
import { getProperty } from './Common.js'
export default function Preloader(props) {
  const image = getProperty(props, "image", "static/dist/img/AdminLTELogo.png")
  return (`<div class="preloader flex-column justify-content-center align-items-center">
        <img class="animation__shake" src="${image}" alt="AdminLTELogo" height="60" width="60"></img>
      </div>`)

}