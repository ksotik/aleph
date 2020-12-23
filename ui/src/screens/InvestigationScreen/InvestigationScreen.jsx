import React, { Component } from 'react';
import queryString from 'query-string';
import { compose } from 'redux';
import { connect } from 'react-redux';
import { Redirect, withRouter } from 'react-router';

import Screen from 'components/Screen/Screen';
import CollectionContextLoader from 'components/Collection/CollectionContextLoader';
import InvestigationViews from 'components/Investigation/InvestigationViews';
import InvestigationWrapper from 'components/Investigation/InvestigationWrapper';
import ErrorScreen from 'components/Screen/ErrorScreen';
import { selectCollection } from 'selectors';

export class InvestigationScreen extends Component {
  render() {
    const { collection, activeMode, activeType } = this.props;

    if (collection.isError) {
      return <ErrorScreen error={collection.error} />;
    }

    if (collection.casefile === false) {
      return <Redirect to={`/datasets/${collection.id}`} />;
    }

    return (
      <CollectionContextLoader>
        <Screen
          title={collection.label}
          description={collection.summary}
        >
          <InvestigationWrapper collection={collection}>
            <InvestigationViews
              collection={collection}
              activeMode={activeMode}
              activeType={activeType}
            />
          </InvestigationWrapper>
        </Screen>
      </CollectionContextLoader>
    );
  }
}

const mapStateToProps = (state, ownProps) => {
  const { collectionId } = ownProps.match.params;
  const { location } = ownProps;
  const hashQuery = queryString.parse(location.hash);
  const activeMode = hashQuery.mode;
  const activeType = hashQuery.type;

  return {
    collection: selectCollection(state, collectionId),
    activeMode,
    activeType,
  };
};


export default compose(
  withRouter,
  connect(mapStateToProps),
)(InvestigationScreen);
