# Changelog
All notable changes to this project will be documented in this file.

## vX.X.X (dd/mm/yyyy)
### Added
None.

### Changed
- (#43) Corrected formula calculating eta by taking square root of 235/strength_class
- (#43) Updated to VIKTOR v14.0.0
- (#43) Default value for calamiteit selectie field in xmlupload editor

### Deprecated
None.

### Removed
None.

### Fixed
None.

### Security
None.

### Internal
None.

## v3.1.3 (13/04/2023)
### Changed
- (#42) Updated to VIKTOR SDK v13.8.0 and python 3.11

## v3.1.2 (13/04/2023)
### Changed
- (#41) Corrected formula used to calculate imperfection factor

## v3.1.1 (04/04/2023)
### Changed
- (#40) Use default value of 1/16 for moment factor

### Fixed
- (#40) Catch empty m_factor to prevent unspecific failing raamwerken calculation

## v3.1.0 (20/03/2023)
### Changed
- () Updated to VIKTOR SDK v13.0.0

## v3.0.5 (02/08/2022)
### Added
- (#39) Integration tests for all methods on XMLupload entity
- (#37) Worst case failing strut is displayed for each strut below the resulting BGT normal
- (#37) Strut fallout calamity BGT can be selected in parametrization and BGT normals are filled in export excel
- (#37) Point load calamity BGT can be selected in parametrization and stootbelasting is filled in export excel
- (#36) Check to determine if profile names are correctly filled in parametrization - Staven tabel
- (#36) Added progress messages during worker analysis
- (#35) Throw userexception on failed connection to generic worker

### Changed
- (#37) Various small edits in parametrization on basis of talk with Arie-Jan
- (#36) Allow for simultaneous Stempel Verwijdering and Puntlast BGT calculations
- (#36) Add angle to spring section and remove from node section in parametrization
- (#36) Slightly refactored XML import and export methods for node angle and profile and material changes
- (#35) Generic worker timeout to 4 minutes

### Deprecated
None.

### Removed
- (#36) Removed profile and material sections in parametrization

### Fixed
- Bug with wall and strut beam angles

### Security
None.

### Internal
None.

## v2.6.6 (28/04/2022)
### Added
None.

### Changed
None.

### Deprecated
None.

### Removed
- Removed memoize worker

### Fixed
None.

### Security
None.

### Internal
None.

## 2.6.5 (10/02/2022)
### Added
None.

### Changed
- (#32) Add Support angle to nodes

### Deprecated
None.

### Removed
None.

### Fixed
None.

### Security
None.

### Internal
None.

## 2.6.4 (11/01/2022)
### Added
None.

### Changed
- unmemoized Worker results for bug fix

### Deprecated
None.

### Removed
None.

### Fixed
None.

### Security
None.

### Internal
None.

## v2.6.3 (20/12/2021)
### Added
None.

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
- (#30) Fixed unit conversion for calculations_purlins["MNy_Rd"]
- (#30) Fixed formula purlins calculation rho
- (#30) Fixed typo MNt -> MNy

### Security
None.

### Internal
None.

## v2.6.2 (20/12/2021)
### Added
None.

### Changed
- (#27) Cleaning of the code 
- (#29) Changed the definition of wall creation and allow angular tolerance of 5 deg

### Deprecated
None.

### Removed
None.

### Fixed
- (#29) The walls numbering goes beyond Z-26

### Security
None.

### Internal
None.


## v2.6.1 (13/12/2021)
### Added
None.

### Changed
- (#26) Changed rendering logic of the Excel download to avoid faulty encoding of Greek letters

### Deprecated
None.

### Removed
- (#26) Removed usage of openpyxl

### Fixed
None.

### Security
None.

### Internal
None.

## v2.6.0 (12/12/2021)
### Added
- (#25) Added header to Overview tab in Excel download
- (#25) Added passing of the point load to the download Excel

### Changed
- (#25) Changed WallView BGT format

### Deprecated
None.

### Removed
None.

### Fixed
- (#25) Fixed Wall consistency userexception
- (#25) Fixed formula Wall BGT length
- (noindex) Fixed angles calculations for download excel

### Security
None.

### Internal
None.

## v2.5.0 (10/12/2021)
### Added
- (#22) Added m_factor as global OptionField
- (#23) Added BGT DataGroup for Wall View
- (#23) Added 'L_BGT_wall' to calculations_purlins df

### Changed
- (#22) Changed a few OptionFields into AutocompleteField

### Deprecated
None.

### Removed
- (#22) Removed m_factor from beam table

### Fixed

### Security
None.

### Internal
None.

## v2.4.0 (03/12/2021)
### Added
- (#19) Added new tabs in the Excel template file

### Changed
- (#21) Wall view: the forces and moment are also displayed
- (#20) Download RTF now as a PDF
- (#15) Staaf lengths are set upon entity creation

### Deprecated
None.

### Removed
None.

### Fixed
None.

### Security
None.

### Internal
None.

## v2.3.1 (26/11/2021)
### Added
- (#17) Stempels & Schoren View: added profiles and distinction type of strut

### Changed
- (#18) Datagroups will now only display the first 100 rows instead of crashing.

### Deprecated
None.

### Removed
None.

### Fixed
- (#18) Fixed the result_df that were limited to 100 rows

### Security
None.

### Internal
None.

## v2.3.0 (17/11/2021)
### Added
- (#16) Added wmf images from Raamwerken

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
None.

### Security
None.

### Internal
None.

## v2.2.0 (16/11/2021)
### Added
- (#14) Added OptionField to select which type of BGT analysis
- (#14) Added calculations for BGT analysis with user-input point load

### Changed
- (#14) UGT calculations is always with point load of 10kN
- (#14) Reformatted Walls Views 

### Deprecated
None.

### Removed
- (#14) Removed for Walls and Gordingen Views, the BGT datagroup

### Fixed
- (#14) Fixed template of Overview table

### Security
None.

### Internal
None.

## v2.1.0 (04/11/2021)
### Added
- (#7) Added distinction between Schoor and stempels
- (#8) Added two DataView for the struts & beams results
- (#9) Added wall logic and maximum uc per wall
- (#9) Added a dedicated function to run analysis of failing struts

### Changed
- (#6) Changed template Excel file for Overview downloable
- (#6) Renamed and refactored big chunky logic
- (#7) Changed the Overzichtstable template
- (#10) Point load is now a parametrization Field

### Deprecated
None.

### Removed
None.

### Fixed
- (#9) Fixed the assignment of YoungModulus=0 to the failing strut.
- (#10) Fixed VED,kop_BGT with addition of extra load
- (#11) Fixed Download XML buttons
- (#12) Fixed calculations differences with Maarten base code.

### Security
None.

### Internal
None.

## v2.0.1 (01/11/2021)
### Added
None.

### Changed
None. 

### Deprecated
None.

### Removed
None.

### Fixed
- (#4) Fixed location template for Raamwerken V6

### Security
None.

### Internal
None.

## v2.0.0 (07/10/2021)
### Added
None.

### Changed
- (#3) Refactored the whole project

### Deprecated
None.

### Removed
None.

### Fixed
None.

### Security
None.

### Internal
None.
