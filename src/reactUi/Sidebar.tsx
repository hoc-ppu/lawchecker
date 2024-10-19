/// <reference types="vite-plugin-svgr/client" />
import UkParliamentSvg from "./assets/ukParliament.svg?react";
import ExpandArrow from "./assets/ExpandArrow.svg?react";
import DocumentIcon from "./assets/documentIcon.svg?react";
import ConferenceIcon from "./assets/conferenceIcon.svg?react";
import BriefcaseIcon from "./assets/briefcaseIcon.svg?react";
import CalenderIcon from "./assets/calenderIcon.svg?react";
import SpeechBubbleIcon from "./assets/speechBubbleIcon.svg?react";

export default function Sidebar() {
  return (
    <div className="side-bar-top-level">
      {/* Begin Contents */}
      <div>
        <div className="figma-sidebar-navigation">
          <div className="logo-header mb-4">
            <a className="concertina" href="#app-home" role="button">
              <UkParliamentSvg />
            </a>
          </div>

          <div id="OP-sidebar-collapsable" className="nav-item-outer-content">
            <div className="op-nav">
              <DocumentIcon />
              <div>Order Paper</div>
            </div>
            <div className="sidebar-expand-arrow">
              <ExpandArrow />
            </div>
          </div>

          <div className="nav-collapsable">
            <div className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href="#get_XML_OP"
                role="button"
                className="concertina nav-item-text"
              >
                Get XML
              </a>
            </div>
            <div className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href="#transform_HTML_OP"
                role="button"
                className="concertina nav-item-text"
              >
                Transform HTML
              </a>
            </div>
            <div className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href="#EMs_For_Hansard_OP"
                role="button"
                className="concertina nav-item-text"
              >
                EMs for Hansard
              </a>
            </div>
          </div>

          <div className="nav-item-outer-content">
            <div className="vnp-nav">
              <ConferenceIcon />

              <div>Votes &amp; Proceedings</div>
            </div>
            <div className="sidebar-expand-arrow">
              <ExpandArrow />
            </div>
          </div>

          <div className="nav-collapsable">
            <div className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href="#get_XML_VP"
                role="button"
                className="concertina nav-item-text"
              >
                Get XML
              </a>
            </div>
            <div className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href="#transform_HTML_VP"
                role="button"
                className="concertina nav-item-text"
              >
                Transform HTML
              </a>
            </div>
          </div>

          <div className="nav-item-outer-content">
            <div className="edms-nav">
              <BriefcaseIcon />

              <div>Early Day Motions</div>
            </div>
            <div className="sidebar-expand-arrow">
              <ExpandArrow />
            </div>
          </div>

          <div className="nav-collapsable">
            <div className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href="#get_XML_EDM"
                role="button"
                className="concertina nav-item-text"
              >
                Get XML
              </a>
            </div>
            <div className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href="#transform_HTML_EDM"
                role="button"
                className="concertina nav-item-text"
              >
                Transform HTML
              </a>
            </div>
          </div>

          <div className="nav-item-outer-content">
            <div className="fdos-nav">
              <CalenderIcon />
              <div>Future Day Orals</div>
            </div>
            <div className="sidebar-expand-arrow">
              <ExpandArrow />
            </div>
          </div>

          <div className="nav-collapsable">
            <div className="nav-collapsable-inner active">
              <div className="seleced-indicator"></div>
              <a
                href="#get_XML_FDO"
                role="button"
                className="concertina nav-item-text"
              >
                Get XML
              </a>
            </div>
            <div className="nav-collapsable-inner">
              <div className="seleced-indicator"></div>
              <a
                href="#transform_HTML_FDO"
                role="button"
                className="concertina nav-item-text"
              >
                Transform HTML
              </a>
            </div>
          </div>

          <div className="nav-item-outer-content">
            <div className="qs-tab-nav">
              <SpeechBubbleIcon />

              <div>Questions Tabled</div>
            </div>
            <div className="sidebar-expand-arrow">
              <ExpandArrow />
            </div>
          </div>

          <div className="nav-collapsable">
            <div className="nav-collapsable-inner active">
              <div className="seleced-indicator"></div>
              <a
                className="concertina nav-item-text"
                href="#get_XML_QT"
                role="button"
              >
                Get XML
              </a>
            </div>
          </div>
        </div>
      </div>

      <div className="version">
        <p>
          <small id="versionInfo">No version info</small>
        </p>
      </div>
    </div>
  );
}
