package kz.qazpost.integration.administrationservice.entities;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Data
@Entity
@Table(schema = "administration", name = "roles")
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class Role {

    @Id
    public String code;
    public String description;
    private Long createdBy;
    private LocalDateTime createdAt;
}