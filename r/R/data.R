# Auto-generated documentation for gbbo datasets
# Generated from models.py and processed tables. Do not edit by hand.

#' Seasons in The Great British Bake Off
#'
#' Season-level metadata, broadcast years, winners, hosts, judges, networks, streaming collections, and filming locations.
#'
#' @format A data frame with 17 rows and 10 variables:
#' \describe{
#'   \item{series_number}{Series / Season number (integer)}
#'   \item{year}{Broadcast premiere year (integer)}
#'   \item{winner}{Series champion baker name}
#'   \item{hosts}{Series presenter(s) / host(s)}
#'   \item{judges}{Series judge(s)}
#'   \item{network}{Broadcasting network (e.g. BBC Two, BBC One, Channel 4)}
#'   \item{pbs_season}{PBS broadcast season number in the US}
#'   \item{netflix_collection}{Netflix Collection number in the US}
#'   \item{roku_season}{The Roku Channel season number}
#'   \item{location}{Filming tent location}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Great_British_Bake_Off}
"seasons"

#' Bakers in The Great British Bake Off
#'
#' Contestant demographics, ages, hometowns, occupations, overall finish placements, and headshot URLs.
#'
#' @format A data frame with 204 rows and 9 variables:
#' \describe{
#'   \item{baker_id}{Unique alphanumeric baker identifier (format: s{series}_{first_name})}
#'   \item{series_number}{Series number (integer)}
#'   \item{name}{Full name of the baker}
#'   \item{age}{Age of the baker during series filming (integer)}
#'   \item{gender}{Gender of the baker ('M', 'F', 'NB')}
#'   \item{occupation}{Stated occupation of the baker}
#'   \item{hometown}{City and region of permanent residence}
#'   \item{overall_placement}{Final rank in the series (1 = Winner)}
#'   \item{image_url}{URL link to official baker headshot photo}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Great_British_Bake_Off}
"bakers"

#' Episodes in The Great British Bake Off
#'
#' Episode-level broadcast metadata, themes, air dates, and challenge time limits.
#'
#' @format A data frame with 158 rows and 8 variables:
#' \describe{
#'   \item{episode_id}{Unique episode identifier (format: s{series}e{episode})}
#'   \item{series_number}{Series number (integer)}
#'   \item{episode_number}{Episode number within the series (integer)}
#'   \item{theme}{Weekly episode theme (e.g. Cake Week, Bread Week)}
#'   \item{air_date}{Original UK television broadcast date (YYYY-MM-DD)}
#'   \item{signature_time_min}{Time limit allocated for Signature challenge in minutes}
#'   \item{technical_time_min}{Time limit allocated for Technical challenge in minutes}
#'   \item{showstopper_time_min}{Time limit allocated for Showstopper challenge in minutes}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Great_British_Bake_Off}
"episodes"

#' Baker Episode Performances in The Great British Bake Off
#'
#' Individual baker challenge bakes, technical rankings, judges' evaluations, Hollywood Handshakes, and weekly outcomes.
#'
#' @format A data frame with 1203 rows and 11 variables:
#' \describe{
#'   \item{performance_id}{Unique performance identifier (format: s{series}e{episode}_{baker_id})}
#'   \item{baker_id}{Foreign key reference to baker identifier}
#'   \item{episode_id}{Foreign key reference to episode identifier}
#'   \item{signature_dish}{Description or title of Signature challenge bake}
#'   \item{technical_rank}{Rank achieved in blind Technical challenge (1 = First Place)}
#'   \item{showstopper_dish}{Description or title of Showstopper challenge bake}
#'   \item{result}{Episode outcome ('STAR_BAKER', 'SAFE', 'ELIMINATED', 'WINNER', 'RUNNER_UP', 'WITHDREW')}
#'   \item{hollywood_handshake}{Logical flag indicating if baker received a Hollywood Handshake}
#'   \item{did_well}{Logical flag indicating if judges commended baker among top of the week}
#'   \item{at_risk}{Logical flag indicating if baker was evaluated as in the bottom / at risk}
#'   \item{absent}{Logical flag indicating if baker was absent due to illness}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Great_British_Bake_Off}
"performances"
