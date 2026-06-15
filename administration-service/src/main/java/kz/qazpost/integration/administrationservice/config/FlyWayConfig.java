package kz.qazpost.integration.administrationservice.config;

import org.flywaydb.core.Flyway;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.flyway.FlywayProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;

@Configuration
@EnableConfigurationProperties(FlywayProperties.class)
public class FlyWayConfig {

    @Autowired
    private DataSource postgresqlDataSource;

    @Bean
    public Flyway flyway() {
        Flyway flyway = Flyway.configure()
                .dataSource(postgresqlDataSource)
                .locations("classpath:db/migration")
                .schemas("administration")
                .defaultSchema("administration")
                .baselineOnMigrate(true)
                .load();
        flyway.migrate();
        return flyway;
    }

}
